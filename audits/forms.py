from django import forms

INPUT_CLASSES = (
    "flex-1 rounded-md border border-slate-300 bg-white px-4 py-2.5 text-sm "
    "text-slate-900 placeholder:text-slate-400 focus:outline-none "
    "focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
)


class URLSubmissionForm(forms.Form):
    url = forms.CharField(
        max_length=2000,
        widget=forms.TextInput(
            attrs={
                "placeholder": "https://example.com",
                "class": INPUT_CLASSES,
                "autocomplete": "off",
            }
        ),
    )

    def clean_url(self):
        url = self.cleaned_data["url"].strip()
        if not url:
            raise forms.ValidationError("Please enter a URL to analyze.")
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        validator = forms.URLField()
        try:
            validator.clean(url)
        except forms.ValidationError:
            raise forms.ValidationError("Enter a valid URL, e.g. https://example.com")
        return url
