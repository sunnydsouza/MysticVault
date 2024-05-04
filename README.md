# 🕵️ MysticVault: Your Personal Chamber of Secrets

![GitHub stars](https://img.shields.io/github/stars/sunnydsouza/MysticVault?style=social)
![GitHub forks](https://img.shields.io/github/forks/sunnydsouza/MysticVault?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/sunnydsouza/MysticVault?style=social)

## 📜 Description

Welcome to **MysticVault**, the magical realm where your digital secrets are guarded under the cloak of advanced encryption. Whether it's personal diaries, family photos, or your stash of ancient spells, **MysticVault** ensures that your private files remain just that—private.

## 🔒 Encryption Details

**MysticVault** uses AES (Advanced Encryption Standard) with a 256-bit key, the same standard used by governments and security agencies worldwide for top-secret information. This means your files are encrypted with a robust, highly secure cipher technique.

### How It Works:
1. **Encryption**: Files are encrypted using a unique key derived from your password combined with a cryptographic salt to enhance security. This process transforms your files into a format that can't be understood without the key.
2. **Decryption**: To access your files, the same password is required to decrypt them back to their original state.

## 🔧 Installation Instructions

1. Clone this repository:
   ```bash
   git clone https://github.com/sunnydsouza/MysticVault.git
   ```
2. Navigate into the project directory:
   ```bash
   cd MysticVault
   ```
3. Install dependencies (don't worry, it's just a sprinkle of digital magic):
   ```bash
   pip install -r requirements.txt
   ```
4. Launch MysticVault and start securing your files:
   ```bash
   python run.py
   ```

### 🚀 Usage

After installing and launching **MysticVault**, the Flask server will be served by default at:

```
http://localhost:5000
```

Navigate to this URL in your web browser to access the MysticVault interface.

### Encryption & Decryption Process:

- **Encryption**: Once you select files for encryption, they will be converted into `.sef` format, and their names will be scrambled to ensure privacy. The original files will be replaced by these encrypted versions in the specified directory.
- **Decryption**: To revert your files to their original state, select the encrypted `.sef` files within the application and enter your password. Successful decryption will restore the original files with their original names and remove the encrypted versions.

### 🐳 Running MysticVault with Docker

Using Docker, you can easily deploy MysticVault without worrying about manually setting up the environment and dependencies. Here’s how you can run MysticVault using Docker:

1. **Build the Docker Image**:
   ```bash
   docker build -t mysticvault .
   ```

2. **Run MysticVault**:
   To run MysticVault in a Docker container and mount a volume for encryption, use the following command. Replace `/path/to/your/folder` with the path to the directory containing the files you wish to encrypt or decrypt.

   ```bash
   docker run -p 5000:5000 -v /path/to/your/folder:/app/data mysticvault
   ```

   This command does the following:
   - `-p 5000:5000`: Maps port 5000 of the container to port 5000 on your host, allowing you to access the server via `localhost:5000`.
   - `-v /path/to/your/folder:/app/data`: Mounts your target directory to the `/app/data` directory inside the container. Ensure that MysticVault is configured to access this directory for file operations.

## 🌟 Distinguishing Features

- **Simple as Pie**: With a user interface cleaner than your grandma's kitchen, encrypting files is as simple as pie. 🥧
- **Files/Folder Support**: Encrypt individual files or entire folders with a single click.
- **Progress Bar/Error Logging**: Keep track of the encryption/decryption process with a handy progress bar and error logging.
- **Docker Support**: Run the app in a Docker container for added security and portability. Can work alongside Plex, Sonarr, Radarr, and other media servers.
- **Photo Friendly**: Got photos? Keep all those memories safe from the nosy parkers!
- **No PhD Required**: You don't need to be a rocket scientist or a cryptographer to use the app. If you can click a button, you're good to go!

## 📸 Screenshots

Here's a sneak peek at what you're getting into:

![App Screenshot](docs/images/Mystic%20Vault%202024-05-04%2010-09-47.png)

✅ ToDo Improvement Points
- Integrate more advanced cryptographic features.
- Improve the drag-and-drop functionality for batch processing.
- Better/Advanced tree view for file management?
- Explore the addition of multi-language support.

## 🤝 Contributing

Got a cool idea or a bug fix? We love contributions!

1. Fork the repo
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin my-new-feature`)
5. Create a new Pull Request

## ☕ Buy Me a Coffee

Loved the app? [Buy me a coffee](https://buymeacoffee.com/sunnydsouza) to keep this project running! ☕

## ⚠️ Disclaimers

- Not responsible for secrets leaked through telepathy or dreams.
- May not protect against determined siblings/mothers-in-law.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.




