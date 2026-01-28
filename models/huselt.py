from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Huselt(models.Model):
    _name = "mandal.helpdesk.huselt"
    _description = "Хүсэлт явуулах хуудас"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Хүсэлтийн нэр", required=True, tracking=True)
    assigned_department_id = fields.Many2one(
        'hr.department', string="Ажлыг оноосон хэлтэс"
    )
    sender_department_id = fields.Many2one(
        'hr.department', string="Илгээсэн хэлтэс"
    )
    description = fields.Text(
        string="Хүсэлтийн тайлбар"
    )

    # Хүсэлт явуулж буй хэрэглэгч
    user_id = fields.Many2one(
        'res.users',
        string="Хүсэлт явуулсан хүн",
        default=lambda self: self.env.user,
        readonly=True
    )

    # Хүсэлт явуулсан хүний ажилтан record (HR)
    employee_id = fields.Many2one(
        'hr.employee',
        string="Хүсэлт явуулсан ажилтан",
        compute="_compute_employee",
        store=True
    )

    # Хэрэглэгчийн хэлтэс
    department_id = fields.Many2one(
        'hr.department',
        string="Хэлтэс",
        related="employee_id.department_id",
        store=True,
        readonly=True
    )


    target_department_id = fields.Many2one(
        'hr.department',
        string="Илгээх хэлтэс",
        tracking=True,
        help="Энд сонгосон хэлтэс рүү хүсэлтийг илгээх. Өөрийн хэлтэс ч сонгож болно."
    )
    # Хүсэлттэй холбоотой Hiih Ajluud
    ajil_ids = fields.One2many(
        'mandal.helpdesk.ajil.onooh',
        'huselt_id',
        string="Хүсэлтийг ажилтанд оноох (Захирал онооно)"
    )

    # Хүсэлт явуулсан хүний ажилтны record-ийг автоматаар авах
    @api.depends('user_id')
    def _compute_employee(self):
        for rec in self:
            employee = self.env['hr.employee'].search(
                [('user_id', '=', rec.user_id.id)],
                limit=1
            )
            rec.employee_id = employee.id if employee else False

    # Хүсэлт үүсгэх үед автоматаар HiihAjluud үүсгэх
    @api.model
    def create(self, vals):
        rec = super().create(vals)

        if not rec.name:
            raise ValidationError("Хүсэлтийн нэр заавал байх ёстой!")

        # Хүсэлт үүсгэхдээ target_department-ийг assigned_department-д хуулах
        if rec.target_department_id:
            rec.assigned_department_id = rec.target_department_id
            
        # Илгээсэн хэлтсийг тохируулах
        if rec.department_id:
            rec.sender_department_id = rec.department_id

        # Автоматаар Ажил оноох бүртгэл үүсгэх
        self.env['mandal.helpdesk.ajil.onooh'].create({
            'name': rec.name,
            'description': rec.description,
            'huselt_id': rec.id,
            'state': 'draft',
            'department_id': rec.assigned_department_id.id if rec.assigned_department_id else False
        })

        return rec

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        user_dep_ids = self.env.context.get('user_department_ids', [])
        if 'assigned_department_id' in fields_list and user_dep_ids:
            res['assigned_department_id'] = user_dep_ids[0]  # Эхний хэлтэс
        return res