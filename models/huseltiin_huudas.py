from odoo import models, fields, api

class Huselt(models.Model):
    _name = "mandal.helpdesk.huselt"
    _description = "daatgaliinhan it-giinhand huselt ilgeeh"
    
    name = fields.Char(string="Ажлын нэр", required=True)
    description = fields.Text(string="Тайлбар")
    
    user_id = fields.Many2one(
        'res.users',
        string="Хүсэлт явуулах хүний нэр",
        default=lambda self: self.env.user,
        readonly=True
    )

    employee_id = fields.Many2one(
        'hr.employee',
        string="Ажилтан",
        compute="_compute_employee",
        store=True
    )

    department_id = fields.Many2one(
        'hr.department',
        string="Хэлтэс",
        related="employee_id.department_id",
        store=True,
        readonly=True
    )

    @api.depends('user_id')  # ЭНЭ ЧУХАЛ!
    def _compute_employee(self):
        for rec in self:
            employee = self.env['hr.employee'].search(
                [('user_id', '=', rec.user_id.id)],
                limit=1
            )
            rec.employee_id = employee.id if employee else False