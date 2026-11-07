from servicems.field_auth import login_context

no_cache = 1


def get_context(context):
	return login_context(context)
