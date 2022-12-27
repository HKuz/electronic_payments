import datetime
import random

import frappe
from frappe.desk.page.setup_wizard.setup_wizard import setup_complete
from erpnext.setup.utils import enable_all_roles_and_domains, set_defaults_for_tests
from erpnext.accounts.doctype.account.account import update_account_number

def before_test():
	frappe.clear_cache()
	today = frappe.utils.getdate()
	setup_complete({
		"currency": "USD",
		"full_name": "Administrator",
		"company_name": "Chelsea Fruit Co",
		"timezone": "America/New_York",
		"company_abbr": "CFC",
		"domains": ["Distribution"],
		"country": "United States",
		"fy_start_date": today.replace(month=1, day=1).isoformat(),
		"fy_end_date": today.replace(month=12, day=31).isoformat(),
		"language": "english",
		"company_tagline": "Chelsea Fruit Co",
		"email": "support@agritheory.dev",
		"password": "admin",
		"chart_of_accounts": "Standard with Numbers",
		"bank_account": "Primary Checking"
	})
	enable_all_roles_and_domains()
	set_defaults_for_tests()
	frappe.db.commit()
	create_test_data()

suppliers = [
	("Exceptional Grid", "Electricity", "Credit Card", 150.00),
	("Liu & Loewen Accountants LLP", "Accounting Services", "Check", 500.00),
	("Mare Digitalis", "Cloud Services", "Credit Card", 200.00),
	("AgriTheory", "ERPNext Consulting", "Check", 1000.00),
	("HIJ Telecom, Inc", "Internet Services", "Check", 150.00),
	("Sphere Cellular", "Phone Services", "Credit Card", 250.00),
	("Cooperative Ag Finance", "Financial Services", "Bank Draft", 5000.00),
]

tax_authority = [
	("Local Tax Authority", "Payroll Taxes", "Check", 0.00),
]

customers = [
	"Andromeda Fruit Market",
	"Betelgeuse Bakery Suppliers",
	"Cassiopeia Restaurant Group",
	"Delphinus Food Distributors",
	"Grus Goodies",
	"Hydra Produce Co",
	"Phoenix Fruit, Ltd"
]


def create_test_data():
	settings = frappe._dict({
		'day': datetime.date(int(frappe.defaults.get_defaults().get('fiscal_year')), 1 ,1),
		'company': frappe.defaults.get_defaults().get('company'),
		'company_account': frappe.get_value("Account",
			{"account_type": "Bank", "company": frappe.defaults.get_defaults().get('company'), "is_group": 0}),
		"warehouse": frappe.get_value("Warehouse",
			{"warehouse_name": "Finished Goods", "company": frappe.defaults.get_defaults().get('company')})
		})
	create_bank_and_bank_account(settings)
	create_suppliers(settings)
	create_customers(customers)
	create_items(settings)
	create_invoices(settings)
	config_expense_claim(settings)
	create_employees(settings)
	create_expense_claim(settings)
	create_payroll_journal_entry(settings)


def create_bank_and_bank_account(settings):
	if not frappe.db.exists('Mode of Payment', 'ACH/EFT'):
		mop = frappe.new_doc('Mode of Payment')
		mop.mode_of_payment = 'ACH/EFT'
		mop.enabled = 1
		mop.type = 'Electronic'
		mop.append('accounts', {'company': settings.company, 'default_account': settings.company_account})
		mop.save()

	#TODO: move these to be created when an Authorize.net or Stripe settings is created
	# if not frappe.db.exists('Mode of Payment', 'Authorize.net Token'):
	# 	mop = frappe.new_doc('Mode of Payment')
	# 	mop.mode_of_payment = 'Authorize.net Token'
	# 	mop.enabled = 1
	# 	mop.type = 'Electronic'
	# 	mop.append('accounts', {'company': settings.company, 'default_account': settings.company_account})
	# 	mop.save()

	# if not frappe.db.exists('Mode of Payment', 'Stripe Token'):
	# 	mop = frappe.new_doc('Mode of Payment')
	# 	mop.mode_of_payment = 'Stripe Token'
	# 	mop.enabled = 1
	# 	mop.type = 'Electronic'
	# 	mop.append('accounts', {'company': settings.company, 'default_account': settings.company_account})
	# 	mop.save()

	frappe.db.set_value('Mode of Payment', 'Wire Transfer', 'type', 'General')
	frappe.db.set_value('Mode of Payment', 'Credit Card', 'type', 'General')
	frappe.db.set_value('Mode of Payment', 'Bank Draft', 'type', 'General')

	if not frappe.db.exists('Bank', 'Local Bank'):
		bank = frappe.new_doc('Bank')
		bank.bank_name = "Local Bank"
		bank.aba_number = '07200091'
		bank.save()

	if not frappe.db.exists('Bank Account', 'Primary Checking - Local Bank'):
		bank_account = frappe.new_doc('Bank Account')
		bank_account.account_name = 'Primary Checking'
		bank_account.bank = bank.name
		bank_account.is_default = 1
		bank_account.is_company_account = 1
		bank_account.company = settings.company
		bank_account.account = settings.company_account
		bank_account.check_number = 2500
		bank_account.company_ach_id = '1381655417'
		bank_account.bank_account_no = '072000915'
		bank_account.branch_code = '07200091'
		bank_account.save()

	doc = frappe.new_doc("Journal Entry")
	doc.posting_date = settings.day
	doc.voucher_type = "Opening Entry"
	doc.company = settings.company
	opening_balance = 50000.00
	doc.append("accounts", {"account": settings.company_account, "debit_in_account_currency": opening_balance})
	retained_earnings = frappe.get_value('Account', {'account_name': "Retained Earnings", 'company': settings.company})
	doc.append("accounts", {"account": retained_earnings, "credit_in_account_currency": opening_balance})
	doc.save()
	doc.submit()

def create_suppliers(settings):
	for supplier in suppliers + tax_authority:
		biz = frappe.new_doc("Supplier")
		biz.supplier_name = supplier[0]
		biz.supplier_group = "Services"
		biz.country = "United States"
		biz.supplier_default_mode_of_payment = supplier[2]
		if biz.supplier_default_mode_of_payment == 'ACH/EFT':
			biz.bank = 'Local Bank'
			biz.bank_account = "123456789"
		biz.currency = "USD"
		biz.default_price_list = "Standard Buying"
		biz.save()

def create_customers(customers):
	for customer in customers:
		cust = frappe.new_doc("Customer")
		cust.customer_name = customer
		cust.customer_type = "Company"
		cust.customer_group = "Commercial"
		cust.territory = "United States"
		cust.tax_id = "04-" +  '{:05d}'.format(random.randint(100,99999)) # Tax ID number
		cust.save()

def create_items(settings):
	for supplier in suppliers + tax_authority:
		item = frappe.new_doc("Item")
		item.item_code = item.item_name = supplier[1]
		item.item_group = "Services"
		item.stock_uom = "Nos"
		item.maintain_stock = 0
		item.is_sales_item, item.is_sub_contracted_item, item.include_item_in_manufacturing = 0, 0, 0
		item.grant_commission = 0
		item.is_purchase_item = 1
		item.append("supplier_items", {"supplier": supplier[0]})
		item.append("item_defaults", {"company": settings.company, "default_warehouse": "", "default_supplier": supplier[0]})
		item.save()
	
	fruits = [
		"Cloudberry",
		"Gooseberry",
		"Damson plum",
		"Tayberry",
		"Hairless rambutan",
		"Kaduka lime",
		"Hackberry"
	]

	for fruit in fruits:
		item = frappe.new_doc("Item")
		item.item_code, item.item_name = fruit.title(), fruit.title()
		item.item_group = "Products"
		item.stock_uom = "Box"
		item.maintain_stock = 1
		item.include_item_in_manufacturing = 0
		item.valuation_rate = round(random.uniform(5,15), 2)
		item.default_warehouse = settings["warehouse"]
		item.description = fruit + " - Box" # Description
		item.default_material_request_type = "Purchase"
		item.valuation_method = "FIFO"
		item.is_purchase_item = 1
		# item.append("supplier_items", {"supplier": random.choice(suppliers)})
		item.save()
		buying_item_price = frappe.new_doc("Item Price")
		buying_item_price.item_code = item.item_code
		buying_item_price.uom = item.stock_uom
		buying_item_price.price_list = "Standard Buying"
		buying_item_price.buying = 1
		buying_item_price.valid_from = "2018-1-1"
		buying_item_price.price_list_rate = round(random.uniform(5,15), 2)
		buying_item_price.save()
		selling_item_price = frappe.new_doc("Item Price")
		selling_item_price.item_code = item.item_code
		selling_item_price.uom = item.stock_uom
		selling_item_price.price_list = "Standard Selling"
		selling_item_price.selling = 1
		selling_item_price.valid_from = "2018-1-1"
		selling_item_price.price_list_rate = round(buying_item_price.price_list_rate * 1.5, 2)
		selling_item_price.save()

def create_invoices(settings):
	# first month - already paid
	for supplier in suppliers:
		pi = frappe.new_doc('Purchase Invoice')
		pi.company = settings.company
		pi.set_posting_time = 1
		pi.posting_date = settings.day
		pi.supplier = supplier[0]
		pi.append('items', {
			'item_code': supplier[1],
			'rate': supplier[3],
			'qty': 1,
		})
		pi.save()
		pi.submit()
	# two electric meters / test invoice aggregation
	pi = frappe.new_doc('Purchase Invoice')
	pi.company = settings.company
	pi.set_posting_time = 1
	pi.posting_date = settings.day
	pi.supplier = suppliers[0][0]
	pi.append('items', {
		'item_code': suppliers[0][1],
		'rate': 75.00,
		'qty': 1,
	})
	pi.save()
	pi.submit()
	# second month - unpaid
	next_day = settings.day + datetime.timedelta(days=31)

	for supplier in suppliers:
		pi = frappe.new_doc('Purchase Invoice')
		pi.company = settings.company
		pi.set_posting_time = 1
		pi.posting_date = next_day
		pi.supplier = supplier[0]
		pi.append('items', {
			'item_code': supplier[1],
			'rate': supplier[3],
			'qty': 1,
		})
		pi.save()
		pi.submit()
	# two electric meters / test invoice aggregation
	pi = frappe.new_doc('Purchase Invoice')
	pi.company = settings.company
	pi.set_posting_time = 1
	pi.posting_date = next_day
	pi.supplier = suppliers[0][0]
	pi.append('items', {
		'item_code': suppliers[0][1],
		'rate': 75.00,
		'qty': 1,
	})
	pi.save()
	pi.submit()


def config_expense_claim(settings):
	try:
		travel_expense_account = frappe.get_value('Account', {'account_name': 'Travel Expenses', 'company': settings.company})
		travel = frappe.get_doc('Expense Claim Type', 'Travel')
		travel.append('accounts', {'company': settings.company, 'default_account': travel_expense_account})
		travel.save()
	except:
		pass

	payroll_payable = frappe.db.get_value('Account', {'account_name': 'Payroll Payable', 'company': settings.company})
	if payroll_payable:
		frappe.db.set_value('Account', payroll_payable, 'account_type', 'Payable')

	if frappe.db.exists('Account', {'account_name': 'Payroll Taxes', 'company': settings.company}):
		return
	pta = frappe.new_doc('Account')
	pta.account_name = "Payroll Taxes"
	pta.account_number = max([int(a.account_number or 1) for a in frappe.get_all('Account', {'is_group': 0},['account_number'])]) + 1
	pta.account_type = "Expense Account"
	pta.company = settings.company
	pta.parent_account = frappe.get_value('Account', {'account_name': 'Indirect Expenses', 'company': settings.company})
	pta.save()


def create_employees(settings):
	for employee_number in range(1, 13):
		emp = frappe.new_doc('Employee')
		emp.first_name = "Test"
		emp.last_name = f"Employee {employee_number}"
		emp.employment_type = "Full-time"
		emp.company = settings.company
		emp.status = "Active"
		emp.gender = "Other"
		emp.date_of_birth = datetime.date(1990, 1, 1)
		emp.date_of_joining = datetime.date(2020, 1, 1)
		emp.mode_of_payment = 'Check' if employee_number % 3 == 0 else 'ACH/EFT'
		emp.mode_of_payment = 'Cash' if employee_number == 10 else emp.mode_of_payment
		emp.expense_approver = 'Administrator'
		if emp.mode_of_payment == 'ACH/EFT':
			emp.bank = 'Local Bank'
			emp.bank_account = f'{employee_number}123456'
		emp.save()


def create_expense_claim(settings):
	cost_center = frappe.get_value('Company', settings.company, 'cost_center')
	payable_acct = frappe.get_value('Company', settings.company, 'default_payable_account')
	# first month - paid
	ec = frappe.new_doc('Expense Claim')
	ec.employee = "HR-EMP-00002"
	ec.expense_approver = "Administrator"
	ec.approval_status = 'Approved'
	ec.append('expenses', {
		'expense_date': settings.day,
		'expense_type': 'Travel',
		'amount': 50.0,
		'sanctioned_amount': 50.0,
		'cost_center': cost_center
	})
	ec.posting_date = settings.day
	ec.company = settings.company
	ec.payable_account = payable_acct
	ec.save()
	ec.submit()
	# second month - open
	next_day = settings.day + datetime.timedelta(days=31)

	ec = frappe.new_doc('Expense Claim')
	ec.employee = "HR-EMP-00002"
	ec.expense_approver = "Administrator"
	ec.approval_status = 'Approved'
	ec.append('expenses', {
		'expense_date': next_day,
		'expense_type': 'Travel',
		'amount': 50.0,
		'sanctioned_amount': 50.0,
		'cost_center': cost_center
	})
	ec.posting_date = next_day
	ec.company = settings.company
	ec.payable_account = payable_acct
	ec.save()
	ec.submit()
	# two expense claims to test aggregation
	ec = frappe.new_doc('Expense Claim')
	ec.employee = "HR-EMP-00002"
	ec.expense_approver = "Administrator"
	ec.approval_status = 'Approved'
	ec.append('expenses', {
		'expense_date': next_day,
		'expense_type': 'Travel',
		'amount': 50.0,
		'sanctioned_amount': 50.0,
		'cost_center': cost_center
	})
	ec.posting_date = next_day
	ec.company = settings.company
	ec.payable_account = payable_acct
	ec.save()
	ec.submit()


def create_payroll_journal_entry(settings):
	emps = frappe.get_list('Employee', {'company': settings.company})
	cost_center = frappe.get_value('Company', settings.company, 'cost_center')
	payroll_account = frappe.get_value('Account', {'company': settings.company, 'account_name': 'Payroll Payable', 'is_group': 0})
	salary_account = frappe.get_value('Account', {'company': settings.company, 'account_name': 'Salary', 'is_group': 0})
	payroll_expense = frappe.get_value('Account', {'company': settings.company, 'account_name': 'Payroll Taxes', 'is_group': 0})
	payable_account= frappe.get_value('Company', settings.company, 'default_payable_account')
	je = frappe.new_doc('Journal Entry')
	je.entry_type = 'Journal Entry'
	je.company = settings.company
	je.posting_date = settings.day
	je.due_date = settings.day
	total_payroll = 0.0
	for idx, emp in enumerate(emps):
		employee_name = frappe.get_value('Employee', {'company': settings.company, 'name': emp.name}, 'employee_name')
		je.append('accounts', {
			'account': payroll_account,
			'bank_account': frappe.get_value("Bank Account", {'account': settings.company_account}),
			'party_type': 'Employee',
			'party': emp.name,
			'cost_center': cost_center,
			'account_currency': 'USD',
			'credit': 1000.00,
			'credit_in_account_currency': 1000.00,
			'debit': 0.00,
			'debit_in_account_currency': 0.00,
			'user_remark': employee_name + ' Paycheck',
			'idx': idx + 2
		})
		total_payroll += 1000.00
	je.append('accounts', {
		'account': salary_account,
		'cost_center': cost_center,
		'account_currency': 'USD',
		'credit': 0.00,
		'credit_in_account_currency': 0.00,
		'debit': total_payroll,
		'debit_in_account_currency': total_payroll,
		'idx': 1,
	})
	je.append('accounts', {
		'account': payroll_expense,
		'cost_center': cost_center,
		'account_currency': 'USD',
		'credit': 0.00,
		'credit_in_account_currency': 0.00,
		'debit': total_payroll * 0.15,
		'debit_in_account_currency': total_payroll * 0.15,
	})
	je.append('accounts', {
		'account': payable_account,
		'cost_center': cost_center,
		'party_type': 'Supplier',
		'party': tax_authority[0][0],
		'account_currency': 'USD',
		'credit': total_payroll * 0.15,
		'credit_in_account_currency':total_payroll * 0.15,
		'debit': 0.00,
		'debit_in_account_currency': 0.0,
	})
	je.save()
	je.submit()
	