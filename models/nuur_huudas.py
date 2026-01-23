from odoo import models, fields, api

class NuurHuudas(models.Model):
    _name = "mandal.helpdesk.nuur"
    _description = "Ajiltnii medeelel"

    user_id = fields.Many2one(
        'res.users',
        string="Nevtersen Hereglegch",
        default=lambda self: self.env.user,
        readonly=True
    )

    job_position_id = fields.Many2one(
        'hr.job',
        string="Job Position",
        compute="_compute_job_position",
        store=True
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string="Ajiltnii Burtgel",
        compute="_compute_employee",
        store=True
    )

    name = fields.Char(
        related="employee_id.name",
        string="Ajiltnii Ner",
        store=True
    )

    job_title = fields.Char(
        related="employee_id.job_title",
        string="Mergejil",
        store=True
    )

    department_id = fields.Many2one(
        related="employee_id.department_id",
        string="Heltes",
        store=True
    )

    @api.depends('user_id')
    def _compute_employee(self):
        for rec in self:
            rec.employee_id = self.env['hr.employee'].search(
                [('user_id', '=', rec.user_id.id)],
                limit=1
            )

    @api.depends('employee_id')
    def _compute_job_position(self):
        for rec in self:
            rec.job_position_id = rec.employee_id.job_id if rec.employee_id else False