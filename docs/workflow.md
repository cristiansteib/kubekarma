
gpg --full-generate-key
gpg --output secring.gpg --export-secret-key HASH
base64 -w0 secring.gpg > secring.gpg.base64


## Create GitHub Repository Secrets
Navigate to your Helm chart repository on GitHub and click on Settings > Secrets > Actions.
 Then click the New repository secret button to create a new secret. Name the secret GPG_KEYRING_BASE64 and paste the contents of your secring.gpg.base64 encoded file from earlier into the Value textbox input and click Add secret to save it
 
Create another secret named GPG_PASSPHRASE. This time enter the passphrase for your PGP secret key in plain text. You should now have two new repository secrets:
