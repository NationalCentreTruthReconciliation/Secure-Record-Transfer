# Frontend Code

The CSS, Javascript, and Typescript files in this directory are built by Webpack. Static files that are not built by Webpack can be found within each Django app.

The static files bundled in this folder can be loaded as Webpack bundles using `render_bundle`. You load bundles by their *name* and the *file type*. For example, this entrypoint's name is `main`:

```js
// In webpack.config.mjs:
{
    entry: {
        main: "./app/frontend/main/index.ts",
    }
}
```

To load this bundle in a template, you can do this:

```jinja
{% load render_bundle from webpack_loader %}
{% render_bundle 'main' 'js' %}
{% render_bundle 'main' 'css' %}
```

The second argument in `render_bundle` is the type of file you want to render. The options are **js** and **css**. If a given entrypoint imports any CSS files, a separate **css** bundle is created, hence why there can be two bundles for one entrypoint.

We use `render_bundle` instead of loading these bundles with the `static` loader because files have content hashes as part of their names. The content hashes change whenever the static assets change, so it's not possible to use a static unchanging name to refer to these built assets. The `render_bundle` tag uses the `dist/webpack-stats.json` file to find a bundle's path given its name which is how we get around the content hash problem.
