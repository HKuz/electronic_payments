frappe.provide('electronic_payments')

frappe.ui.form.on('Sales Invoice', {
	refresh: (frm) => {
		frm.add_custom_button(__('Electronic Payments'), () => {
			electronic_payments.electronic_payments(frm);
		});
	}
});