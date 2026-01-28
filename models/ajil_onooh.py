from odoo import models, fields, api
from odoo.exceptions import AccessError, ValidationError

class AjilOnooh(models.Model):
    _name = "mandal.helpdesk.ajil.onooh"
    _description = "Ажил оноох – зөвхөн хэлтсийн захирал хэрэглэдэг"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # 🔹 Холбогдох хүсэлт
    huselt_id = fields.Many2one(
        'mandal.helpdesk.huselt',
        string="Холбогдох хүсэлт",
        ondelete='cascade',
        required=True
    )

    # 🔹 Холбогдсон ажил
    ajil_id = fields.Many2one(
        'mandal.helpdesk.ajil',
        string="Оноож буй ажил",
        ondelete='cascade'
    )
    
    # 🔹 Хэлтэс
    department_id = fields.Many2one(
        'hr.department',
        string="Хариуцах хэлтэс",
        tracking=True,
        help="Энэ ажлыг хариуцах хэлтэс"
    )

    deadline = fields.Date(string="Дуусах хугацаа", tracking=True)
    start_date = fields.Datetime(string="Эхлэх огноо", tracking=True)
    end_date = fields.Datetime(string="Дуусах огноо", tracking=True)

    progress = fields.Integer(string="Гүйцэтгэл (%)", default=0, tracking=True)

    state = fields.Selection([
        ('draft', 'Ноорог'),
        ('assigned', 'Хүн авсан'),
        ('in_progress', 'Явагдаж байна'),
        ('done', 'Гүйцэтгэсэн'),
        ('cancel', 'Цуцлагдсан')
    ], default='draft', string="Төлөв", tracking=True)

    name = fields.Char(
        string="Ажлын нэр",
        required=True,
        tracking=True
    )
    description = fields.Text(string="Ажлын тайлбар")

    assigned_user_id = fields.Many2one(
        'res.users',
        string="Оноосон ажилтан",
        tracking=True,
        help="Энэ ажлыг хариуцах ажилтан"
    )
    
    # Үүсгэсэн хэрэглэгч
    creator_id = fields.Many2one(
        'res.users',
        string="Үүсгэсэн",
        default=lambda self: self.env.user,
        readonly=True
    )

    def _check_is_boss(self):
        """Захирал эсэхийг шалгах"""
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)],
            limit=1
        )
        # Захирал эсвэл group_helpdesk_boss бүлэгт багтсан эсэхийг шалгах
        is_boss_group = self.env.user.has_group('helpdesk.group_helpdesk_boss')
        is_boss_job = employee and employee.job_id and 'boss' in employee.job_id.name.lower()
        
        if not (is_boss_group or is_boss_job):
            raise AccessError("Зөвхөн Захирал энэ үйлдлийг хийх эрхтэй!")

    @api.model
    def create(self, vals):
        """Ажил үүсгэх - Захирал хийнэ"""
        # Draft төлөвтэй үүсгэх үед захирал шалгахгүй
        if vals.get('state', 'draft') != 'draft':
            self._check_is_boss()
        return super().create(vals)

    def write(self, vals):
        """Ажил засварлах"""
        # Ажилтан оноохдоо захирал шалгах
        if 'assigned_user_id' in vals:
            self._check_is_boss()
        return super().write(vals)

    def unlink(self):
        """Ажил устгах - Захирал хийнэ"""
        self._check_is_boss()
        return super().unlink()

    def action_assign(self):
        """Ажилтанд оноох үйлдэл"""
        self._check_is_boss()
        for rec in self:
            if not rec.assigned_user_id:
                raise ValidationError("Ажилтан сонгоно уу!")
            
            # Ажил үүсгэх
            ajil = self.env['mandal.helpdesk.ajil'].create({
                'name': rec.name,
                'description': rec.description,
                'huselt_id': rec.huselt_id.id,
                'assigned_user_id': rec.assigned_user_id.id,
                'department_id': rec.department_id.id,
                'state': 'assigned',
                'ajil_onooh_id': rec.id
            })
            
            rec.write({
                'ajil_id': ajil.id,
                'state': 'assigned',
                'start_date': fields.Datetime.now()
            })
            
            rec.message_post(
                body=f"Ажил {rec.assigned_user_id.name}-д оноогдлоо.",
                subject="Ажил оноогдсон"
            )

    def action_start(self):
        """Ажил эхлүүлэх"""
        for rec in self:
            rec.state = 'in_progress'
            if rec.ajil_id:
                rec.ajil_id.state = 'in_progress'
            rec.message_post(body="Ажил эхэллээ.")

    def action_done(self):
        """Ажил дуусгах"""
        for rec in self:
            rec.write({
                'state': 'done',
                'end_date': fields.Datetime.now(),
                'progress': 100
            })
            if rec.ajil_id:
                rec.ajil_id.state = 'done'
            rec.message_post(body="Ажил амжилттай дууслаа.")

    def action_cancel(self):
        """Ажил цуцлах"""
        for rec in self:
            rec.state = 'cancel'
            if rec.ajil_id:
                rec.ajil_id.state = 'cancel'
            rec.message_post(body="Ажил цуцлагдлаа.")

    # 🔹 Default context-аас huselt_id авах
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'huselt_id' in fields_list and self.env.context.get('default_huselt_id'):
            res['huselt_id'] = self.env.context['default_huselt_id']
        return res

    # 🔹 View-д зөвхөн Huselt-ээр filter хийх
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.env.context.get('filter_huselt_id'):
            huselt_id = self.env.context['filter_huselt_id']
            args = [('huselt_id', '=', huselt_id)] + args
        return super().search(args, offset=offset, limit=limit, order=order, count=count)