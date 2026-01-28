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
        required=False  # Changed to False to allow editing in draft state
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

    can_edit_fields = fields.Boolean(
        compute='_compute_can_edit_fields'
    )

    @api.depends()
    def _compute_can_edit_fields(self):
        for rec in self:
            rec.can_edit_fields = self.env.user.has_group('helpdesk.group_helpdesk_boss')

    @api.onchange('huselt_id')
    def _onchange_huselt_id(self):
        """Хүсэлт сонгоход department автоматаар тохируулагдана"""
        if self.huselt_id and self.huselt_id.assigned_department_id:
            self.department_id = self.huselt_id.assigned_department_id

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

    @api.constrains('start_date')
    def _check_start_date_not_changed(self):
        """Start date cannot be manually changed after moving out of draft state"""
        for rec in self:
            if rec.start_date and rec.id and rec.state not in ['draft']:
                original = self.browse(rec.id)
                if original.start_date != rec.start_date:
                    raise ValidationError("Эхлэх огноог өөрчлөх боломжгүй!")

    @api.constrains('end_date')
    def _check_end_date_not_changed(self):
        """End date cannot be manually changed after completion"""
        for rec in self:
            if rec.end_date and rec.id and rec.state not in ['draft', 'assigned', 'in_progress']:
                original = self.browse(rec.id)
                if original.end_date != rec.end_date:
                    raise ValidationError("Дуусах огноог өөрчлөх боломжгүй!")

    @api.model
    def create(self, vals):
        """Ажил үүсгэх - Захирал хийнэ"""
        # Draft төлөвтэй үүсгэх үед захирал шалгахгүй
        if vals.get('state', 'draft') != 'draft':
            self._check_is_boss()
        
        # Ensure department is set from huselt if huselt is provided
        if 'department_id' not in vals and vals.get('huselt_id'):
            huselt = self.env['mandal.helpdesk.huselt'].browse(vals['huselt_id'])
            if huselt and huselt.assigned_department_id:
                vals['department_id'] = huselt.assigned_department_id.id
        
        return super().create(vals)

    def write(self, vals):
        """Ажил засварлах - Захирал шалгах"""
        for rec in self:
            # In draft state, boss can edit all fields freely
            if rec.state == 'draft':
                # Only check boss permission if assigning user
                if 'assigned_user_id' in vals and vals.get('assigned_user_id'):
                    self._check_is_boss()
            else:
                # After draft state, enforce stricter rules
                # Check start_date and end_date
                if 'start_date' in vals and rec.start_date:
                    raise ValidationError("Эхлэх огноог өөрчлөх боломжгүй!")
                
                if 'end_date' in vals and rec.end_date:
                    raise ValidationError("Дуусах огноог өөрчлөх боломжгүй!")
                
                # Prevent changing huselt, department, and assigned user after draft
                if 'huselt_id' in vals and rec.huselt_id:
                    raise ValidationError("Холбогдох хүсэлтийг өөрчлөх боломжгүй!")
                
                if 'department_id' in vals and rec.department_id:
                    raise ValidationError("Хэлтсийг өөрчлөх боломжгүй!")
                
                if 'assigned_user_id' in vals and rec.assigned_user_id:
                    self._check_is_boss()
                
            # Progress update validation
            if 'progress' in vals:
                # if rec.state not in ['in_progress', 'done']:
                #     raise ValidationError("Гүйцэтгэлийг зөвхөн 'Явагдаж байна' эсвэл 'Дуусгах' төлөвт шинэчлэх боломжтой!")
                if vals['progress'] < 0 or vals['progress'] > 100:
                    raise ValidationError("Гүйцэтгэл 0-100% хооронд байх ёстой!")
        
        return super().write(vals)

    def unlink(self):
        """Ажил устгах - Захирал хийнэ"""
        self._check_is_boss()
        
        # Only allow deletion in draft or canceled state
        for rec in self:
            if rec.state not in ['draft', 'cancel']:
                raise ValidationError("Зөвхөн ноорог эсвэл цуцлагдсан ажлыг устгах боломжтой!")
        
        return super().unlink()

    def action_assign(self):
        """Ажилтанд оноох үйлдэл"""
        self._check_is_boss()
        for rec in self:
            if not rec.assigned_user_id:
                raise ValidationError("Ажилтан сонгоно уу!")
            
            # Validate department is set
            if not rec.department_id:
                raise ValidationError("Хариуцах хэлтэс сонгоно уу!")
            
            # Validate huselt is set
            if not rec.huselt_id:
                raise ValidationError("Холбогдох хүсэлт сонгоно уу!")
            
            # Ажил үүсгэх
            ajil = self.env['mandal.helpdesk.ajil'].create({
                'name': rec.name or "Шинэ ажил",
                'description': rec.description or "",
                'huselt_id': rec.huselt_id.id if rec.huselt_id else False,
                'assigned_user_id': rec.assigned_user_id.id,  # Fixed variable name
                'department_id': rec.department_id.id if rec.department_id else False,
                'state': 'assigned',
                'ajil_onooh_id': rec.id if rec else False,
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
            if rec.state != 'assigned':
                raise ValidationError("Зөвхөн оноогдсон ажлыг эхлүүлэх боломжтой!")
            
            rec.state = 'in_progress'
            if rec.ajil_id:
                rec.ajil_id.state = 'in_progress'
            # rec.message_post(body="Ажил эхэллээ.")

    def action_done(self):
        """Ажил дуусгах"""
        for rec in self:
            if rec.state != 'in_progress':
                raise ValidationError("Зөвхөн явагдаж буй ажлыг дуусгах боломжтой!")
            
            rec.write({
                'state': 'done',
                'end_date': fields.Datetime.now(),
                'progress': 100
            })
            if rec.ajil_id:
                rec.ajil_id.state = 'done'
            # rec.message_post(body="Ажил амжилттай дууслаа.")

    def action_cancel(self):
        """Ажил цуцлах"""
        for rec in self:
            if rec.state == 'done':
                raise ValidationError("Дууссан ажлыг цуцлах боломжгүй!")
            
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
    def search(self, domain, offset=0, limit=None, order=None):
        if self.env.context.get('filter_huselt_id'):
            huselt_id = self.env.context['filter_huselt_id']
            domain = [('huselt_id', '=', huselt_id)] + domain
        return super().search(domain, offset=offset, limit=limit, order=order)