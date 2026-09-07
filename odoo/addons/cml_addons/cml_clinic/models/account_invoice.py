import logging
from odoo import fields, models, api
_logger = logging.getLogger(__name__)


try:
    from odoo.addons.membership.models.membership import STATE
except ImportError:
    _logger.warning("Cannot import 'membership' addon.")
    _logger.debug("Details", exc_info=True)


class Invoice(models.Model):
    _inherit = 'account.invoice'
    _description = 'Description'

    membership_state = fields.Selection(
        string='Membership Status',
        selection=STATE, store=True, index=True,
        related="partner_id.membership_state"
    )

