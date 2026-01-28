{
    'name': 'Mandal Help Desk Module',
    'version': '1.0.7',
    'license': 'LGPL-3',
    'summary': 'Хэлтэс доторх ажлын хүсэлт, удирдлагын систем',
    'description': '''
    Хэлтсийн ажилчид бусад хэлтэс эсвэл өөрийн хэлтэст ажлын хүсэлт гаргах,
    захирал ажил оноох, ажлын урсгалыг хянах систем.
    ''',
    'author': 'myeirban bilimkhan',
    'depends': ['base', 'hr', 'mail'],
    'data': [
        #'security/helpdesk_groups.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/actions.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
}