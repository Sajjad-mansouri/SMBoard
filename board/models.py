from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from .fields import OrderField

UserModel = get_user_model()

class DateAbstractModel(models.Model):
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True

def board_image_path(instance, file_name):
	created = timezone.now()
	return "{owner}/{board}/board_files/{year}/{month}/{day}/{file_name}".format(
										owner=instance.owner_id,
										board=instance.name, 
										year = created.year ,
										month = created.month,
										day = created.day,
										file_name = file_name)

class Board(DateAbstractModel):
	STATUS_CHOICES = [
	("private", "Private"),
	("workspace", "Workspace"),
	("public", "Public")
	]
	owner = models.ForeignKey(UserModel, on_delete=models.CASCADE, verbose_name=_("User"), related_name="user_boards")
	name = models.CharField(_("Name"), max_length=250)
	status = models.CharField(_("Status"), choices=STATUS_CHOICES, max_length=10, default="workspace")
	background_color = models.CharField(_("Background Color"), max_length=7, help_text="format:#00fca8", blank=True)
	background_image = models.ImageField(_("Background Image"), upload_to=board_image_path, null=True, blank=True)
	closed = models.BooleanField(_("Closed"), default=False)




	def __str__(self):
		return f"{self.owner} board: {self.name}"

	class Meta:
		verbose_name = _("Board")
		verbose_name_plural = _("Boards")


class BoardMembership(DateAbstractModel):
	MEMBER_TYPES = [
		("admin", "Admin"),
		("member", "Member"),
		("observer", "Observer"),
		("guest", "Guest")
	]
	user = models.ForeignKey(UserModel, on_delete=models.CASCADE, verbose_name=_("User"), related_name="user_memberships")
	board = models.ForeignKey(Board, on_delete=models.CASCADE, verbose_name=_("Board"), related_name="board_memberships")
	member_type = models.CharField(_("Member Type"), choices=MEMBER_TYPES, max_length=8)
	accepted = models.BooleanField(_("Accepted"), default=False)



	def __str__(self):
		return f"{self.user} is {self.board} board {self.member_type} member"

	class Meta:
		verbose_name = _("Board Member")
		verbose_name_plural = _("Boards Members")
		constraints = [
			models.UniqueConstraint(
				fields = ["user", "board"],
				name = "user_board_unique"
				)
		]


def list_cover_path(instance, file_name):

	return "{owner}/{board}/list_files/{list}/{year}/{month}/{day}/{file_name}".format(
										owner=instance.board.owner_id,
										board=instance.board.name, 
										list=instance.name,
										year = created.year ,
										month = created.month,
										day = created.day,
										file_name = file_name)
class BoardList(DateAbstractModel):
	order = OrderField(_("Order"), blank=True)
	board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="board_lists", verbose_name="Board")
	name = models.CharField(_("Name"), max_length=250)
	cover_image = models.ImageField(_("Conver Image"), upload_to=list_cover_path, null=True, blank=True)
	cover_color = models.CharField(_("Background Color"), max_length=7, help_text="format:#00fca8", blank=True)
	archived = models.BooleanField(_("Archived"), default=False)



	def __str__(self):
		return f"{self.name} is list of  {self.board.owner} {self.board} board "

	class Meta:
		verbose_name = _("List")
		verbose_name_plural = _("Lists")
		ordering = ["order"]


def card_cover_path(instance, file_name):

	return "{owner}/{board}/{card}/card_cover/{list}/{year}/{month}/{day}/{file_name}".format(
										owner=instance.board_list.board.owner_id,
										board=instance.board_list.board.name, 
										list=instance.board_list.name,
										card=instance.name,
										year = instance.created.year ,
										month = instance.created.month,
										day = instance.created.day,
										file_name = file_name)
class Card(DateAbstractModel):
	order = OrderField(_("Order"), blank=True)

	board_list = models.ForeignKey(BoardList, on_delete=models.CASCADE, related_name="list_cards", verbose_name="Board List")
	name = models.CharField(_("Name"), max_length=250)
	description = models.TextField(_("Description"), blank=True)
	start_date = models.DateField(_("Start Date"), null=True, blank=True)
	due_date = models.DateTimeField(_("Due Date"), null=True, blank=True)
	completed = models.BooleanField(_("Completed"),default=False)
	archived = models.BooleanField(_("Archived"), default=False)
	cover_image = models.ImageField(_("Conver Image"), upload_to=card_cover_path, null=True, blank=True)
	cover_image_fk = models.ForeignKey("CardImage", on_delete=models.SET_NULL, null=True, blank=True, related_name="cards")
	cover_color = models.CharField(_("Background Color"), max_length=7, help_text="format:#00fca8", blank=True)




	def __str__(self):
		return f"{self.name} is card of  {self.board_list} list "

	class Meta:
		verbose_name = _("Card")
		verbose_name_plural = _("Cards")
		ordering = ["order"]


class CardMembership(DateAbstractModel):
	user = models.ForeignKey(UserModel, on_delete=models.CASCADE, verbose_name=_("User"), related_name="carduser_memberships")
	card = models.ForeignKey(Card, on_delete=models.CASCADE, verbose_name=_("Card"), related_name="card_memberships")

	def __str__(self):
		return f"{self.user} is {self.card} card member"

	class Meta:
		verbose_name = _("Card Member")
		verbose_name_plural = _("Cards Members")
		constraints = [
			models.UniqueConstraint(
				fields = ["user", "card"],
				name = "user_card_unique"
				)
		]
class CardLabel(DateAbstractModel):
	card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="card_labels", verbose_name="Card")
	name = models.CharField(_("Name"), max_length=250)
	color = models.CharField(_("Color"), max_length=7, help_text="format:#00fca8")


	def __str__(self):
		return f"{self.name} is {self.card} label"

	class Meta:
		verbose_name = _("Label")
		verbose_name_plural = _("Labels")


class CheckList(DateAbstractModel):
	card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="card_checklists", verbose_name="Card")
	name = models.CharField(_("Name"), max_length=250)

	def __str__(self):
		return f"{self.name} is {self.card} checklist"

	class Meta:
		verbose_name = _("CheckList")
		verbose_name_plural = _("CheckLists")

class ChecklistItem(DateAbstractModel):
	checklist = models.ForeignKey(CheckList, on_delete=models.CASCADE, related_name="checklist_items", verbose_name="CheckList")
	name = models.CharField(_("Name"), max_length=250)
	is_completed = models.BooleanField(_("is completed"), default=False)


	def __str__(self):
		return f"{self.name} is {self.checklist} checklist {self.is_completed}"

	class Meta:
		verbose_name = _("CheckList Item")
		verbose_name_plural = _("CheckLists Items")


def attachment_path(instance, file_name):
	created = timezone.now()
	card = instance.card
	board_list = card.board_list
	board = board_list.board
	user = board.owner_id
	return "{owner}/{board}/{list}/{card}/card_attachments/{year}/{month}/{day}/{file_name}".format(
										owner=user,
										board=board.name, 
										list=board_list.name,
										card=card.name,
										year = created.year ,
										month = created.month,
										day = created.day,
										file_name = file_name)
class AttachmentAbstractModel(DateAbstractModel):
	name = models.CharField(_("Name"), max_length=250, blank=True)
	description = models.TextField(_("Description"), blank=True)
	card = models.ForeignKey(Card, on_delete=models.CASCADE, verbose_name="Card")
	user = models.ForeignKey(UserModel, on_delete=models.CASCADE, verbose_name=_("User"))

	class Meta:
		abstract = True
class CardFile(AttachmentAbstractModel):
	file = models.FileField(_("File"), upload_to=attachment_path)

	def __str__(self):
		return f"{self.user} file"

	class Meta:
		verbose_name = _("File Attachment")
		verbose_name_plural = _("File Attachments")
	def get_name(self):
		name_loc = self.file.name
		name = name_loc.rsplit("/",1)[1]
		return name

class CardImage(AttachmentAbstractModel):
	file = models.ImageField(_("Image"), upload_to=attachment_path)

	def __str__(self):
		return f"{self.user} image"

	class Meta:
		verbose_name = _("Image Attachment")
		verbose_name_plural = _("Image Attachments")

	def get_name(self):
		name_loc = self.file.name
		name = name_loc.rsplit("/",1)[1]
		return name

class Comment(DateAbstractModel):
	user = models.ForeignKey(UserModel, on_delete=models.CASCADE, verbose_name=_("User"), related_name="user_comments")
	card = models.ForeignKey(Card, on_delete=models.CASCADE, verbose_name="Card", related_name="card_comments")
	reply_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
	reply_object_id = models.PositiveIntegerField(null=True)
	reply_content_object = GenericForeignKey('reply_content_type', 'reply_object_id')
	content = models.TextField()
	edited = models.BooleanField(_("Edited"), default=False)

	def __str__(self):
		return f"{self.user} comment {self.card}"

	class Meta:
		verbose_name = _("Comment")
		verbose_name_plural = _("Comments")
		ordering = ["-created"]



class CardWatch(DateAbstractModel):
	user = models.ForeignKey(UserModel, on_delete=models.CASCADE, verbose_name=_("User"), related_name="user_cardwatchs")
	card = models.ForeignKey(Card, on_delete=models.CASCADE, verbose_name="Card", related_name="card_cardwatchs")
	watch = models.BooleanField(_("Watch"), default=False)

	def __str__(self):
		watch = "watch" if self.watch else "dont watch" 
		return f"{self.user} {watch} {self.card}"

	class Meta:
		verbose_name = _("Card Watch")
		verbose_name_plural = _("Card Watchs")


class BoardWatch(DateAbstractModel):
	user = models.ForeignKey(UserModel, on_delete=models.CASCADE, verbose_name=_("User"), related_name="user_boardwatchs")
	board = models.ForeignKey(Board, on_delete=models.CASCADE, verbose_name="Board", related_name="board_boardwatchs")
	watch = models.BooleanField(_("Watch"), default=False)

	def __str__(self):
		watch = "watch" if self.watch else "dont watch" 
		return f"{self.user} {watch} {self.board}"

	class Meta:
		verbose_name = _("Board Watch")
		verbose_name_plural = _("Board Watchs")