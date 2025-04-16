import inspect
import logging
import types
from typing import Any

from .._internal.constants import USING_PYDANTIC

if USING_PYDANTIC:
    import pydantic

from ..http import Endpoint, Response
from . import ListenerManager


class RequestListenerManager(ListenerManager):
    """CaptureListenerManager"""

    def __init__(self) -> None:
        """
        The __init__ function is called when the class is instantiated.
        It sets up the instance variables that will be used by other methods
        in the class.


        :param self: Refer to the class instance
        :return: A dictionary of the capture listeners and request listeners
        """
        super().__init__()

    async def notify(
        self, endpoint: Endpoint, response: Response, extra_value: Any
    ) -> Any:
        """
        The on_request function is called when a request has been made to the
        endpoint.
        The response object contains all the information about the request

        :param self: Refer to the class instance
        :param endpoint: Endpoint: Get the endpoint that was called
        :param response: Response: Get the response from the endpoint
        :return: The result of the call function
        """

        def filter_annotations(annotations: list[Any]) -> Any:
            for item in annotations:
                if issubclass(item, pydantic.BaseModel):
                    yield item

        if not (listener := self.get_listener(endpoint)):
            return None
        logger = logging.getLogger('squarecloud')
        kwargs: dict[str, Any] = {}
        call_params = listener.callback_params
        call_extra_param: inspect.Parameter | None = call_params.get('extra')
        annotation: Any | None = None

        if 'response' in call_params.keys():
            kwargs['response'] = response
        if 'extra' in call_params.keys():
            kwargs['extra'] = extra_value

        if call_extra_param:
            annotation = call_extra_param.annotation
        if (
            call_extra_param is not None
            and annotation is not None
            and annotation != call_extra_param.empty
            and USING_PYDANTIC
        ):
            annotation = call_extra_param.annotation
            cast_result = self.cast_to_pydantic_model(annotation, extra_value)
            if not cast_result:
                msg: str = (
                    f'a "{annotation.__name__}"'
                    if not isinstance(annotation, types.UnionType)
                    else str(
                        [
                            x.__name__
                            for x in filter_annotations(
                                list(annotation.__args__)
                            )
                        ]
                    )
                )
                logger.warning(
                    'Failed on cast extra argument in '
                    f'"{listener.callback.__name__}" into '
                    f'{msg}.\n'
                    f'The listener has been skipped.',
                    extra={'type': 'listener'},
                )
                return None
            kwargs['extra'] = cast_result
        is_coro: bool = inspect.iscoroutinefunction(listener.callback)
        try:
            if is_coro:
                listener_result = await listener.callback(**kwargs)
            else:
                listener_result = listener.callback(**kwargs)
            logger.info(
                f'listener "{listener.callback.__name__}" was invoked.\n'
                f'Endpoint: {listener.endpoint}\n'
                f'RETURN: {listener_result}\n',
                extra={'type': 'listener'},
            )
            return listener_result
        except Exception as exc:
            logger.error(
                f'Failed to call listener "{listener.callback.__name__}.\n'
                f'Error: {exc.__repr__()}.\n',
                extra={'type': 'listener'},
            )
            if listener.config.force_raise:
                raise exc
