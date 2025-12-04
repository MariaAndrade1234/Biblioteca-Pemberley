import logging
from rest_framework import viewsets

logger = logging.getLogger(__name__)


class BaseViewSet(viewsets.ModelViewSet):

	def handle_exception(self, exc):
		try:
			logger.exception('Exception in %s: %s', self.__class__.__name__, exc)
		except Exception:
			pass
		return super().handle_exception(exc)

