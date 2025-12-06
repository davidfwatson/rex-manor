# Rex Manor Website

This repository contains the source code for the Rex Manor neighborhood association website, built using the Hugo static site generator.

## Project Structure

The project is structured as follows:

-   **`config.toml`**: Contains the main configuration for the Hugo site, such as the base URL, language, and title.
-   **`content/`**: Contains the content files for the site, including the homepage (`index.md`) and an about page (`about.md`).
-   **`layouts/`**: Contains the HTML templates that define the structure and layout of the website.
    -   `_default/baseof.html`: Base template for all pages.
    -   `_default/list.html`: Template for list pages.
    -   `partials/head.html`: Partial template to define the header of the page.
-   **`static/`**: Contains static files such as CSS, images, etc.
    - `css/style.css`: Contains the CSS code for the web pages.

## Usage

To use this website, you need to have Hugo installed on your system.

1.  Install Hugo.
2.  Clone this repository.
3.  Customize the configuration files.
4.  Run `hugo server`.

## Deployment Workflow

This project uses GitHub Actions for deployment:

1. **Create a PR** - Push your branch and create a pull request. This automatically deploys to **staging**.
2. **Merge to main** - Once the PR is merged, the changes are automatically deployed to **production**.

## Contributing

Contributions are welcome! If you have any suggestions or improvements, please create a pull request.

## License

This project is licensed under the terms of the MIT license.
