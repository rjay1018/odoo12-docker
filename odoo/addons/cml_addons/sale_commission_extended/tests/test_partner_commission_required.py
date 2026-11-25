from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestPartnerCommissionRequired(TransactionCase):

    def setUp(self):
        super(TestPartnerCommissionRequired, self).setUp()
        self.Partner = self.env['res.partner']
        self.Commission = self.env['sale.commission']
        self.commission = self.Commission.create({
            'name': 'Test Pct Commission',
            'commission_type': 'pct',
            'fix_qty': 5.0,
        })
        self.agent = self.Partner.create({
            'name': 'Test Sales Agent',
            'agent': True,
            'customer': False,
            'supplier': True,
            'commission': self.commission.id,
        })

    def test_new_customer_without_commission_raises(self):
        with self.assertRaises(ValidationError):
            self.Partner.create({
                'name': 'Customer Missing Agent',
                'customer': True,
                'agent': False,
            })

    def test_new_customer_with_commission_succeeds(self):
        customer = self.Partner.create({
            'name': 'Customer With Agent',
            'customer': True,
            'agent': False,
            'partner_categ_comm_ids': [(0, 0, {
                'agent_id': self.agent.id,
                'commission_id': self.commission.id,
            })],
        })
        self.assertEqual(len(customer.partner_categ_comm_ids), 1)

    def test_new_vendor_without_commission_succeeds(self):
        vendor = self.Partner.create({
            'name': 'Test Vendor',
            'customer': False,
            'supplier': True,
        })
        self.assertTrue(vendor.exists())

    def test_new_agent_without_commission_succeeds(self):
        agent = self.Partner.create({
            'name': 'Another Agent',
            'customer': True,
            'agent': True,
        })
        self.assertTrue(agent.exists())

    def test_new_child_contact_without_commission_succeeds(self):
        parent = self.Partner.create({
            'name': 'Parent Customer',
            'customer': True,
            'partner_categ_comm_ids': [(0, 0, {
                'agent_id': self.agent.id,
                'commission_id': self.commission.id,
            })],
        })
        child = self.Partner.create({
            'name': 'Branch Contact',
            'customer': True,
            'parent_id': parent.id,
        })
        self.assertEqual(child.parent_id, parent)

    def test_install_mode_skips_validation(self):
        partner = self.Partner.with_context(install_mode=True).create({
            'name': 'Install Mode Customer',
            'customer': True,
        })
        self.assertTrue(partner.exists())

    def test_write_existing_customer_without_commission_succeeds(self):
        partner = self.Partner.with_context(install_mode=True).create({
            'name': 'Existing Customer',
            'customer': True,
        })
        partner.write({'name': 'Existing Customer Updated'})
        self.assertEqual(partner.name, 'Existing Customer Updated')

    def test_new_user_creation_succeeds(self):
        user = self.env['res.users'].create({
            'name': 'New Internal User',
            'login': 'new_internal_user_test',
        })
        self.assertTrue(user.exists())
        self.assertTrue(user.partner_id.exists())

    def test_non_sales_user_can_create_customer_with_commission(self):
        base_user_group = self.env.ref('base.group_user')
        user = self.env['res.users'].create({
            'name': 'Non Sales User',
            'login': 'non_sales_user_test',
            'groups_id': [(6, 0, [base_user_group.id])],
        })
        view = self.Partner.sudo(user.id).fields_view_get(view_type='form')
        self.assertIn('arch', view)
        customer = self.Partner.sudo(user.id).create({
            'name': 'Customer Created By Non Sales User',
            'customer': True,
            'agent': False,
            'partner_categ_comm_ids': [(0, 0, {
                'agent_id': self.agent.id,
                'commission_id': self.commission.id,
            })],
        })
        self.assertEqual(len(customer.partner_categ_comm_ids), 1)

