import asyncio
import logging

from infinity_emb.engine import AsyncEngineArray, EngineArgs
from infinity_emb.primitives import ModelNotDeployedError
from PIL import Image

from config import EmbeddingServiceConfig
from src.multimodal_utils import parse_input_item
from utils import (
    ModelInfo,
    OpenAIModelInfo,
    list_embeddings_to_response,
    to_rerank_response,
)

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.config = EmbeddingServiceConfig()
        engine_args = []
        for model_name, batch_size, dtype in zip(
            self.config.model_names, self.config.batch_sizes, self.config.dtypes
        ):
            engine_args.append(
                EngineArgs(
                    model_name_or_path=model_name,
                    batch_size=batch_size,
                    engine=self.config.backend,
                    dtype=dtype,
                    model_warmup=False,
                    lengths_via_tokenize=True,
                )
            )

        self.engine_array = AsyncEngineArray.from_args(engine_args)
        self.is_running = False
        self.sepamore = asyncio.Semaphore(1)

    async def start(self):
        """starts the engine background loop"""
        async with self.sepamore:
            if not self.is_running:
                await self.engine_array.astart()
                self.is_running = True

    async def stop(self):
        """stops the engine background loop"""
        async with self.sepamore:
            if self.is_running:
                await self.engine_array.astop()
                self.is_running = False

    async def route_openai_models(self) -> OpenAIModelInfo:
        return OpenAIModelInfo(
            data=[ModelInfo(id=model_id, stats={}) for model_id in self.list_models()]
        ).model_dump()

    def list_models(self) -> list[str]:
        return list(self.engine_array.engines_dict.keys())

    async def route_openai_get_embeddings(
        self,
        embedding_input: str | list[str] | list[str | bytes | Image.Image],
        model_name: str,
        return_as_list: bool = False,
    ):
        """
        Returns embeddings for the input text and/or images.
        Supports mixed text and image inputs while preserving order.
        """
        if not self.is_running:
            await self.start()

        available_models = self.list_models()
        if model_name not in available_models:
            logger.error(
                f"Requested model '{model_name}' not found. "
                f"Available models: {available_models}"
            )
            raise ValueError(
                f"Model '{model_name}' is not available. "
                f"Available models: {', '.join(available_models)}"
            )

        if not isinstance(embedding_input, list):
            embedding_input = [embedding_input]

        parsed_items = await asyncio.gather(
            *[parse_input_item(item) for item in embedding_input]
        )

        # Separate text and image items while tracking their original indices
        text_items = []
        text_indices = []
        image_items = []
        image_indices = []

        for idx, (item_type, processed_data) in enumerate(parsed_items):
            if item_type == "text":
                text_items.append(processed_data)
                text_indices.append(idx)
            else:  # item_type == 'image'
                image_items.append(processed_data)
                image_indices.append(idx)

        logger.info(
            f"Processing embeddings for model '{model_name}': "
            f"{len(text_items)} text items, {len(image_items)} image items "
            f"(total: {len(embedding_input)} items)"
        )

        text_embeddings = []
        text_usage = 0
        image_embeddings = []
        image_usage = 0

        if text_items:
            logger.debug(f"Calling .embed() with {len(text_items)} text items")
            text_embeddings, text_usage = await self.engine_array[model_name].embed(
                text_items
            )
            logger.debug(f"Successfully got {len(text_embeddings)} text embeddings")

        if image_items:
            logger.debug(f"Calling .image_embed() with {len(image_items)} image items")
            try:
                image_embeddings, image_usage = await self.engine_array[
                    model_name
                ].image_embed(images=image_items)
                logger.debug(
                    f"Successfully got {len(image_embeddings)} image embeddings"
                )
            except ModelNotDeployedError as e:
                error_msg = (
                    f"Model '{model_name}' does not support image embeddings. "
                    f"Please use a multimodal model (e.g., 'jinaai/jina-clip-v1') "
                    f"or provide text-only input. Found {len(image_items)} image items in the request."
                )
                logger.error(f"{error_msg} Original error: {e}")
                raise ValueError(error_msg) from e

        # Merge embeddings back in original order
        total_items = len(embedding_input)
        ordered_embeddings: list = [None] * total_items

        for idx, embedding in zip(text_indices, text_embeddings):
            ordered_embeddings[idx] = embedding

        for idx, embedding in zip(image_indices, image_embeddings):
            ordered_embeddings[idx] = embedding

        total_usage = text_usage + image_usage

        if return_as_list:
            return [
                list_embeddings_to_response(
                    ordered_embeddings,
                    model=model_name,
                    usage=total_usage,  # type: ignore[arg-type]
                )
            ]
        else:
            return list_embeddings_to_response(
                ordered_embeddings,
                model=model_name,
                usage=total_usage,  # type: ignore[arg-type]
            )

    async def infinity_rerank(
        self, query: str, docs: str, return_docs: str, model_name: str
    ):
        """Rerank the documents based on the query"""
        if not self.is_running:
            await self.start()
        scores, usage = await self.engine_array[model_name].rerank(
            query=query, docs=docs, raw_scores=False
        )
        if not return_docs:
            docs = None
        return to_rerank_response(
            scores=scores, documents=docs, model=model_name, usage=usage
        )
