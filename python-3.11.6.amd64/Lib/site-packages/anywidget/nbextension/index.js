// package.json
var name = "anywidget";
var version = "0.7.1";

// src/widget.js
function is_href(str) {
  return str.startsWith("http://") || str.startsWith("https://");
}
async function load_css_href(href, anywidget_id) {
  let prev = document.querySelector(`link[id='${anywidget_id}']`);
  if (prev) {
    let newLink = (
      /** @type {HTMLLinkElement} */
      prev.cloneNode()
    );
    newLink.href = href;
    newLink.addEventListener("load", () => prev?.remove());
    prev.after(newLink);
    return;
  }
  return new Promise((resolve) => {
    let link = Object.assign(document.createElement("link"), {
      rel: "stylesheet",
      href,
      onload: resolve
    });
    document.head.appendChild(link);
  });
}
function load_css_text(css_text, anywidget_id) {
  let prev = document.querySelector(`style[id='${anywidget_id}']`);
  if (prev) {
    prev.textContent = css_text;
    return;
  }
  let style = Object.assign(document.createElement("style"), {
    id: anywidget_id,
    type: "text/css"
  });
  style.appendChild(document.createTextNode(css_text));
  document.head.appendChild(style);
}
async function load_css(css, anywidget_id) {
  if (!css)
    return;
  if (is_href(css))
    return load_css_href(css, anywidget_id);
  return load_css_text(css, anywidget_id);
}
async function load_esm(esm) {
  if (is_href(esm)) {
    return import(
      /* webpackIgnore: true */
      esm
    );
  }
  let url = URL.createObjectURL(new Blob([esm], { type: "text/javascript" }));
  let widget;
  try {
    widget = await import(
      /* webpackIgnore: true */
      url
    );
  } catch (e) {
    console.log(e);
    throw e;
  }
  URL.revokeObjectURL(url);
  return widget;
}
function extract_context(view) {
  let model = {
    get: view.model.get.bind(view.model),
    set: view.model.set.bind(view.model),
    save_changes: view.model.save_changes.bind(view.model),
    send: view.model.send.bind(view.model),
    // @ts-expect-error
    on(name2, callback) {
      view.model.on(name2, callback, view);
    },
    off(name2, callback) {
      view.model.off(name2, callback, view);
    },
    widget_manager: view.model.widget_manager
  };
  return { model, el: view.el };
}
function widget_default({ DOMWidgetModel, DOMWidgetView }) {
  class AnyModel extends DOMWidgetModel {
    static model_name = "AnyModel";
    static model_module = name;
    static model_module_version = version;
    static view_name = "AnyView";
    static view_module = name;
    static view_module_version = version;
    /** @param {Parameters<InstanceType<DOMWidgetModel>["initialize"]>} args */
    initialize(...args) {
      super.initialize(...args);
      this.on("change:_css", () => {
        let id = this.get("_anywidget_id");
        if (!id)
          return;
        console.debug(`[anywidget] css hot updated: ${id}`);
        load_css(this.get("_css"), id);
      });
      this.on("change:_esm", async () => {
        let id = this.get("_anywidget_id");
        if (!id)
          return;
        console.debug(`[anywidget] esm hot updated: ${id}`);
        let views = (
          /** @type {unknown} */
          Object.values(this.views ?? {})
        );
        for await (
          let view of
          /** @type {Promise<AnyView>[]} */
          views
        ) {
          let widget = await load_esm(this.get("_esm"));
          try {
            await view._anywidget_cached_cleanup();
          } catch (e) {
            console.warn("[anywidget] error cleaning up previous module.", e);
            view._anywidget_cached_cleanup = () => {
            };
          }
          this.off(null, null, view);
          view.$el.empty();
          let cleanup = await widget.render(extract_context(view));
          view._anywidget_cached_cleanup = cleanup ?? (() => {
          });
        }
      });
    }
    /**
     * @param {Record<string, any>} state
     *
     * We override to support binary trailets because JSON.parse(JSON.stringify()) doesnt
     * propeprty clone binary data (it just returns an empty object).
     *
     * https://github.com/jupyter-widgets/ipywidgets/blob/47058a373d2c2b3acf101677b2745e14b76dd74b/packages/base/src/widget.ts#L562-L583
     */
    serialize(state) {
      let serializers = (
        /** @type {DOMWidgetModel} */
        this.constructor.serializers || {}
      );
      for (let k of Object.keys(state)) {
        try {
          let serialize = serializers[k]?.serialize;
          if (serialize) {
            state[k] = serialize(state[k], this);
          } else {
            state[k] = structuredClone(state[k]);
          }
          if (typeof state[k]?.toJSON === "function") {
            state[k] = state[k].toJSON();
          }
        } catch (e) {
          console.error("Error serializing widget state attribute: ", k);
          throw e;
        }
      }
      return state;
    }
  }
  class AnyView extends DOMWidgetView {
    async render() {
      await load_css(this.model.get("_css"), this.model.get("_anywidget_id"));
      let widget = await load_esm(this.model.get("_esm"));
      let cleanup = await widget.render(extract_context(this));
      this._anywidget_cached_cleanup = cleanup ?? (() => {
      });
    }
    /** @type {() => Promise<void> | void} */
    _anywidget_cached_cleanup() {
    }
    async remove() {
      await this._anywidget_cached_cleanup();
      return super.remove();
    }
  }
  return { AnyModel, AnyView };
}

// src/index.js
define(["@jupyter-widgets/base"], widget_default);
