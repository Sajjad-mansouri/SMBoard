from django.db import models
from django.core.exceptions import ObjectDoesNotExist

class OrderField(models.PositiveIntegerField):

	def pre_save(self, model_instance, add):
		if getattr(model_instance, self.attname) is None:
			try:
				qs = self.model.objects.filter(board__owner=model_instance.board.owner)
				last_item = qs.latest(self.attname)
				value = last_item.order + 1
			except ObjectDoesNotExist:
				value = 0
			setattr(model_instance, self.attname, value)
			return value

		else:
			return super().pre_save(model_instance, add)