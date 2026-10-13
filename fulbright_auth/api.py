import frappe
from frappe import _
from frappe.rate_limiter import rate_limit


def _email_link_limit() -> int:
	return 5


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=_email_link_limit, seconds=60 * 60)
def send_login_link(email: str):
	"""Email a one-time link that opens the Fulbright app."""
	email = (email or "").strip()
	if not email:
		frappe.throw(_("Email is required"))

	expiry = int(frappe.get_system_settings("login_with_email_link_expiry") or 10)
	if not frappe.db.exists("User", {"name": email, "enabled": 1}):
		return

	key = frappe.generate_hash()
	frappe.cache.set_value(
		f"one_time_login_key:{key}",
		email,
		expires_in_sec=expiry * 60,
	)

	app_url = (frappe.conf.get("fulbright_app_url") or "http://localhost:3000").rstrip("/")
	if not app_url.startswith(("http://", "https://")):
		frappe.throw(_("fulbright_app_url must start with http:// or https://"))

	link = f"{app_url}/login/link?key={key}"
	frappe.sendmail(
		recipients=email,
		subject=_("Sign in to Fulbright"),
		message=_(
			"Use this link to sign in. It expires in {0} minutes.<br><br><a href='{1}'>Sign in</a>"
		).format(expiry, link),
		now=True,
	)
