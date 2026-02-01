from ..constants import _UPPERCASE_WORDS_TO_IGNORE

def convert_to_user_prop(hysys_prop: str):
	user_prop = ""

	i = 0
	while i <= len(hysys_prop) - 1:
		user_prop += hysys_prop[i]

		if i + 1 <= len(hysys_prop) - 1 and   \
			hysys_prop[i].islower() and hysys_prop[i + 1].isupper():
			user_prop += " "
		elif i + 1 <= len(hysys_prop) - 1 and \
			hysys_prop[i].isnumeric() and hysys_prop[i + 1].isupper():
			user_prop += " "
		elif i + 2 <= len(hysys_prop) - 1 and \
			hysys_prop[i].isupper() and       \
			hysys_prop[i + 1].isupper() and   \
			hysys_prop[i + 2].islower() and   \
			hysys_prop[i:i + 2] not in _UPPERCASE_WORDS_TO_IGNORE:
			user_prop += " "

		i += 1

	return user_prop