{
    'name': 'Axx Reverse Charge',
    'summary': 'Axx Reverse Charge',
    'description': """
            If Reverse charge valid articles total > 5000 then those articles (product) 
            taxes should be removed based on order type.
            Update tax based on the article category!
            Income account and Expense account will also be updated for these articles if RC valid amount > 5000
        """,
    'category': 'Accounting',
    'version': '16.0.1.0.1',
    'author': 'axxelia GmbH',
    'website': 'http://www.axxelia.com',
    'depends': [
        # ---------------------
        # Odoo
        # ---------------------
        'sale_management',
        'purchase',
        'stock',
        # ---------------------
        # OCA
        # ---------------------
        # ---------------------
        # EE
        # ---------------------
        'account_accountant',
        # ---------------------
        # Thirdparty
        # ---------------------
        # ---------------------
        # Axxelia
        # ---------------------
        # ---------------------
        # PROJECT
        # ---------------------

    ],
    'data': [
        # Security
        # Wizards
        # Data
        # views
        'views/product/product_category_views.xml',
        'views/sale/sale_order_views.xml',
        'views/purchase/purchase_order_views.xml',
        # Menus
        # Reports
        # Templates
    ],
    'installable': True,
    'application': True
}
