# Fast Stone Clone App

### Pre-requisites 

1. Get `credentials.json` file from <a href="https://console.cloud.google.com/project">Google Console</a>.
   1. <a href="/workspace/guides/create-project">Create a Google Cloud project</a>  for your
   Google Workspace app, extension, or integration.
   2. <a href="/workspace/guides/enable-apis">Enable the Google Drive APIs</a> 
      in your Google Cloud project.
   3. <a href="/workspace/guides/configure-oauth-consent">Configure OAuth consent</a> to ensure users can 
   understand and approve what access your app has to their data and get `credentials.json` file. 
   4. Add (Copy) `credentials.json` file to the project directory `\fast_stone_clone_app`

### Google Drive

Each directory for **client** should have public access:  
1. Under “**General access**” click the Down &#8681;.
2. Choose "**Anyone with the link**".

### How to install it:

1. First Step
```commandline
install_python.bat
```

2. Second Step
```commandline
runner.bat
```
