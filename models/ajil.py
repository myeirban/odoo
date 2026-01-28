from odoo import models, fields, api
from odoo.exceptions import AccessError, ValidationError

class Ajil(models.Model):
    _name = 'mandal.helpdesk.ajil'
    _description = 'Тухайн ажилтны хэлтэст ирсэн ажлууд'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Ажлын нэр", required=True, tracking=True)
    description = fields.Text(string="Тайлбар")

    huselt_id = fields.Many2one(
        'mandal.helpdesk.huselt',
        string="Холбогдох хүсэлт",
        readonly=True
    )

    ajil_onooh_id = fields.Many2one(
        'mandal.helpdesk.ajil.onooh',
        string="Ажил оноох бүртгэл",
        readonly=True
    )

    assigned_user_id = fields.Many2one(
        'res.users',
        string="Хариуцсан ажилтан",
        tracking=True,
        required=False
    )

    creator_user_id = fields.Many2one(
        'res.users',
        string="Үүсгэсэн хэрэглэгч",
        default=lambda self: self.env.user,
        readonly=True
    )

    department_id = fields.Many2one(
        'hr.department',
        string="Хэлтэс",
        tracking=True
    )

    state = fields.Selection([
        ('draft', 'Ноорог'),
        ('assigned', 'Хүн авсан'),
        ('in_progress', 'Явагдаж байна'),
        ('done', 'Гүйцэтгэсэн'),
        ('cancel', 'Цуцлагдсан')
    ], default='draft', string="Төлөв", tracking=True)

    priority = fields.Selection([
        ('low', 'Бага'),
        ('medium', 'Дунд'),
        ('high', 'Өндөр')
    ], default='medium', string="Анхаарал")

    deadline = fields.Date(string="Дуусах хугацаа")
    start_date = fields.Datetime(string="Эхлэх огноо")
    end_date = fields.Datetime(string="Дуусах огноо")

    progress = fields.Integer(string="Гүйцэтгэл (%)", default=0, tracking=True)

    can_view = fields.Boolean(
        compute="_compute_can_view",
        store=False
    )

    @api.depends('assigned_user_id', 'creator_user_id', 'department_id')
    def _compute_can_view(self):
        """Хэрэглэгч энэ ажлыг харах эрхтэй эсэхийг тодорхойлох"""
        current_user = self.env.user
        user_departments = current_user.employee_ids.mapped('department_id')
        for rec in self:
            rec.can_view = (
                rec.department_id in user_departments or
                rec.assigned_user_id == current_user or
                rec.creator_user_id == current_user
            )

    def action_accept(self):
        """Ажлыг хүлээн авах - Зөвхөн оноогдсон ажилтан"""
        for rec in self:
            if rec.assigned_user_id != self.env.user:
                raise AccessError("Зөвхөн танд оноогдсон ажлыг хүлээн авч болно!")
            
            rec.write({
                'state': 'assigned',
                'start_date': fields.Datetime.now()
            })
            rec.message_post(body="Ажлыг хүлээн авлаа.")

    def action_start(self):
        """Ажил эхлүүлэх"""
        for rec in self:
            if rec.state != 'assigned':
                raise ValidationError("Зөвхөн хүлээн авсан ажлыг эхлүүлж болно!")
            
            rec.write({
                'state': 'in_progress',
                'start_date': fields.Datetime.now() if not rec.start_date else rec.start_date
            })
            rec.message_post(body="Ажил эхэллээ.")

    def action_done(self):
        """Ажил дуусгах"""
        for rec in self:
            rec.write({
                'state': 'done',
                'end_date': fields.Datetime.now(),
                'progress': 100
            })
            
            # Холбогдсон ajil_onooh record-ийг мөн шинэчлэх
            if rec.ajil_onooh_id:
                rec.ajil_onooh_id.write({
                    'state': 'done',
                    'end_date': fields.Datetime.now(),
                    'progress': 100
                })
            
            rec.message_post(body="Ажил амжилттай дууслаа.")

    def action_cancel(self):
        """Ажил цуцлах"""
        for rec in self:
            rec.state = 'cancel'
            rec.message_post(body="Ажил цуцлагдлаа.")

    @api.model
    def get_my_tasks(self):
        """Надад оноогдсон ажлууд"""
        return self.search([
            ('assigned_user_id', '=', self.env.user.id)
        ])

    @api.model
    def get_my_department_tasks(self):
        """Миний хэлтсийн ажлууд"""
        user_departments = self.env.user.employee_ids.mapped('department_id')
        return self.search([
            ('department_id', 'in', user_departments.ids)
        ])

    @api.model
    def get_my_created_tasks(self):
        """Миний үүсгэсэн ажлууд"""
        return self.search([
            ('creator_user_id', '=', self.env.user.id)
        ])