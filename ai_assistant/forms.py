from django import forms

from .models import AIPlatformSettings
from .security import encrypt_secret, masked_secret


class AIPlatformSettingsForm(forms.ModelForm):
    gapgpt_api_key = forms.CharField(required=False, widget=forms.PasswordInput(render_value=False),
                                     label="کلید GapGPT")
    tavily_api_key = forms.CharField(required=False, widget=forms.PasswordInput(render_value=False),
                                     label="کلید Tavily")

    class Meta:
        model = AIPlatformSettings
        exclude = ("gapgpt_api_key_encrypted", "tavily_api_key_encrypted")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["gapgpt_api_key"].help_text = masked_secret(self.instance.get_gapgpt_api_key())
        self.fields["tavily_api_key"].help_text = masked_secret(self.instance.get_tavily_api_key())

    def save(self, commit=True):
        instance = super().save(commit=False)
        gapgpt = self.cleaned_data.get("gapgpt_api_key")
        tavily = self.cleaned_data.get("tavily_api_key")
        if gapgpt:
            instance.gapgpt_api_key_encrypted = encrypt_secret(gapgpt)
        if tavily:
            instance.tavily_api_key_encrypted = encrypt_secret(tavily)
        if commit:
            instance.save()
        return instance
