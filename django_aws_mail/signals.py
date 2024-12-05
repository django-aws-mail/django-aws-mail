from django.dispatch import Signal

mail_pre_send = Signal()
mail_post_send = Signal()

mail_bounce = Signal()
mail_complaint = Signal()
mail_delivery = Signal()
mail_delivery_delay = Signal()
mail_send = Signal()
mail_reject = Signal()
mail_open = Signal()
mail_click = Signal()
