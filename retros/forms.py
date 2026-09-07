from django import forms


class CreateRetroForm(forms.Form):
    name = forms.CharField(required=True)
    description = forms.CharField(required=False, widget=forms.Textarea)
    participant_limit = forms.IntegerField(required=False)
    pin = forms.CharField(required=True, widget=forms.PasswordInput)

    def clean_participant_limit(self):
        participant_limit = self.cleaned_data.get("participant_limit")
        if participant_limit is not None and participant_limit <= 0:
            raise forms.ValidationError("Participant limit must be greater than zero.")
        return participant_limit
