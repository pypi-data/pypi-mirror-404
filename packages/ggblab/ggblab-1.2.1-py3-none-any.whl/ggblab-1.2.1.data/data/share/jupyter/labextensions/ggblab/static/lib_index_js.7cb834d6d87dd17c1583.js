"use strict";
(self["webpackChunkggblab"] = self["webpackChunkggblab"] || []).push([["lib_index_js"],{

/***/ "./lib/index.js"
/*!**********************!*\
  !*** ./lib/index.js ***!
  \**********************/
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _jupyterlab_application__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyterlab/application */ "webpack/sharing/consume/default/@jupyterlab/application");
/* harmony import */ var _jupyterlab_application__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_application__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @jupyterlab/apputils */ "webpack/sharing/consume/default/@jupyterlab/apputils");
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _jupyterlab_settingregistry__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @jupyterlab/settingregistry */ "webpack/sharing/consume/default/@jupyterlab/settingregistry");
/* harmony import */ var _jupyterlab_settingregistry__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_settingregistry__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @jupyterlab/ui-components */ "webpack/sharing/consume/default/@jupyterlab/ui-components");
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_3__);
/* harmony import */ var _widget__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./widget */ "./lib/widget.js");
/* harmony import */ var _jupyterlab_services__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! @jupyterlab/services */ "webpack/sharing/consume/default/@jupyterlab/services");
/* harmony import */ var _jupyterlab_services__WEBPACK_IMPORTED_MODULE_5___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_services__WEBPACK_IMPORTED_MODULE_5__);
/* harmony import */ var _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! @jupyterlab/coreutils */ "webpack/sharing/consume/default/@jupyterlab/coreutils");
/* harmony import */ var _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_6___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_6__);
/* harmony import */ var _package_json__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ../package.json */ "./package.json");


// ILauncher removed: launcher integration is not used in this build

//import { DockLayout } from '@lumino/widgets';




// Import package.json to reflect the package version in the UI log.

var CommandIDs;
(function (CommandIDs) {
    CommandIDs.create = 'ggblab:create';
})(CommandIDs || (CommandIDs = {}));
// const PANEL_CLASS = 'jp-ggblabPanel';
/**
 * Initialization data for the ggblab extension.
 */
const plugin = {
    id: 'ggblab:plugin',
    description: 'A JupyterLab extension.',
    autoStart: true,
    optional: [_jupyterlab_settingregistry__WEBPACK_IMPORTED_MODULE_2__.ISettingRegistry, _jupyterlab_application__WEBPACK_IMPORTED_MODULE_0__.ILayoutRestorer],
    activate: (app, settingRegistry, restorer) => {
        console.debug(`JupyterLab extension ggblab-${_package_json__WEBPACK_IMPORTED_MODULE_7__.version} is activated!`);
        // Note: widget manager global registration removed — no global registrar
        // is installed. WidgetManager must be passed explicitly via `widgetManager`
        // in the widget creation args when available.
        // Pre-register comm targets for any kernels visible to the front-end
        // KernelManager. This helps accept `comm_open` messages that arrive
        // before a widget mounts. Factor the logic into a function so we can
        // re-run it when sessions change (e.g. kernels start/stop).
        const defaultCommTarget = 'ggblab-comm';
        const registered = new Set();
        const scanAndRegisterKernels = async () => {
            console.debug('ggblab: scanAndRegisterKernels start');
            console.debug('ggblab: currently registered (start)', Array.from(registered));
            try {
                const base = _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_6__.PageConfig.getBaseUrl() || '/';
                const token = _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_6__.PageConfig.getToken();
                const serverSettings = _jupyterlab_services__WEBPACK_IMPORTED_MODULE_5__.ServerConnection.makeSettings({
                    baseUrl: base,
                    token,
                    appendToken: true
                });
                const registerKernel = async (kid, model) => {
                    console.debug('ggblab: registerKernel called', kid);
                    console.debug('ggblab: registerKernel model snapshot', model && typeof model === 'object' ? { id: model.id, name: model.name } : model);
                    if (!kid) {
                        console.debug('ggblab: registerKernel - empty kid, skipping');
                        return;
                    }
                    if (registered.has(kid)) {
                        console.debug('ggblab: registerKernel - already registered', kid);
                        return;
                    }
                    try {
                        window.__ggblab_comm_store =
                            window.__ggblab_comm_store || {};
                        const store = window.__ggblab_comm_store;
                        // Prefer using an existing live kernel connection object when
                        // the `model` argument already exposes `registerCommTarget`.
                        // This ensures we attach to the same frontend-managed connection
                        // that receives comm_open messages from the kernel. If `model`
                        // is only a kernel model object, fall back to creating a
                        // dedicated `KernelConnection` instance.
                        const kernel = (model && typeof model.registerCommTarget === 'function')
                            ? model
                            : new _jupyterlab_services__WEBPACK_IMPORTED_MODULE_5__.KernelConnection({ model, serverSettings });
                        try {
                            console.debug('ggblab: using KernelConnection for registration', { id: (kernel === null || kernel === void 0 ? void 0 : kernel.id) || (model && model.id) || null, hasRegister: typeof kernel.registerCommTarget === 'function' });
                        }
                        catch (ee) {
                            console.debug('ggblab: unable to inspect kernel connection', ee);
                        }
                        console.debug('ggblab: calling registerCommTarget on KernelConnection', kid, defaultCommTarget);
                        kernel.registerCommTarget(defaultCommTarget, (commOp, msg) => {
                            console.debug('ggblab: registerCommTarget handler invoked', { kernelId: kid, msgSummary: msg && msg.content ? Object.keys(msg.content) : null });
                            try {
                                store[kid] = commOp;
                                // Ensure by-id and queue stores exist
                                window.__ggblab_comm_by_id =
                                    window.__ggblab_comm_by_id || {};
                                window.__ggblab_comm_queue =
                                    window.__ggblab_comm_queue || {};
                                // Attempt to determine comm id from the incoming message or comm object
                                let commId = null;
                                try {
                                    commId = (msg && msg.content && msg.content.comm_id) ||
                                        (commOp && (commOp.comm_id || commOp.commId || commOp.commId)) ||
                                        null;
                                }
                                catch (ee) {
                                    commId = null;
                                }
                                if (commId) {
                                    try {
                                        window.__ggblab_comm_by_id[commId] = commOp;
                                        try {
                                            window.__ggblab_comm_by_id[commId].__ggblab_meta = {
                                                source: 'pre-registered',
                                                kernelId: kid,
                                                when: new Date().toISOString()
                                            };
                                        }
                                        catch (ee) {
                                            /* ignore metadata attach errors */
                                        }
                                        console.debug('[ggblab] pre-registered frontend comm by id', kid, commId);
                                    }
                                    catch (ee) {
                                        console.warn('ggblab: failed to store comm by id', ee);
                                    }
                                }
                                else {
                                    // If no comm id yet, push the open message into a queue keyed by kernel id
                                    try {
                                        window.__ggblab_comm_queue = window.__ggblab_comm_queue || {};
                                        window.__ggblab_comm_queue[kid] = window.__ggblab_comm_queue[kid] || [];
                                        window.__ggblab_comm_queue[kid].push(msg || {});
                                        console.debug('[ggblab] queued comm open message for kernel', kid);
                                    }
                                    catch (ee) {
                                        console.warn('ggblab: failed to queue comm open message', ee);
                                    }
                                }
                                // Attach logging handlers to commOp for debugging
                                try {
                                    const prevOnMsg = commOp.onMsg;
                                    commOp.onMsg = (m) => {
                                        try {
                                            const now = new Date().toISOString();
                                            const mid = (m && m.content && m.content.comm_id) || commId || (commOp && (commOp.comm_id || commOp.commId)) || null;
                                            console.debug('[ggblab] comm.onMsg', { when: now, kernelId: kid, commId: mid, msg: m });
                                        }
                                        catch (ee) {
                                            console.debug('[ggblab] comm.onMsg (logging failed)', ee);
                                        }
                                        try {
                                            if (typeof prevOnMsg === 'function')
                                                prevOnMsg(m);
                                        }
                                        catch (ee) {
                                            /* ignore handler errors */
                                        }
                                    };
                                }
                                catch (ee) {
                                    /* ignore */
                                }
                                try {
                                    const prevOnClose = commOp.onClose;
                                    commOp.onClose = (m) => {
                                        try {
                                            const now = new Date().toISOString();
                                            const closedId = (m && m.content && m.content.comm_id) || commId || (commOp && (commOp.comm_id || commOp.commId)) || null;
                                            console.debug('[ggblab] comm.onClose', { when: now, kernelId: kid, commId: closedId, msg: m });
                                        }
                                        catch (ee) {
                                            console.debug('[ggblab] comm.onClose (logging failed)', ee);
                                        }
                                        try {
                                            if (typeof prevOnClose === 'function')
                                                prevOnClose(m);
                                        }
                                        catch (ee) {
                                            /* ignore */
                                        }
                                    };
                                }
                                catch (ee) {
                                    /* ignore */
                                }
                                console.debug('[ggblab] pre-registered frontend comm', kid);
                                try {
                                    // mark the per-kernel store comm with metadata for widget lookup
                                    try {
                                        store[kid].__ggblab_meta = {
                                            source: 'pre-registered',
                                            kernelId: kid,
                                            when: new Date().toISOString()
                                        };
                                    }
                                    catch (ee) {
                                        /* ignore */
                                    }
                                }
                                catch (ee) {
                                    /* ignore */
                                }
                            }
                            catch (e) {
                                console.warn('ggblab: failed to store pre-registered comm', e);
                            }
                        });
                        registered.add(kid);
                        console.debug('ggblab: registerKernel - registered', kid);
                        console.debug('ggblab: currently registered (after add)', Array.from(registered));
                        try {
                            // Attempt to create a frontend-originated "pre-warm" comm
                            // so widgets mounting shortly after kernel registration
                            // can reuse an already-open comm instead of recreating one.
                            if (typeof kernel.createComm === 'function') {
                                try {
                                    const preComm = kernel.createComm(defaultCommTarget);
                                    try {
                                        const prevOnMsg = preComm.onMsg;
                                        preComm.onMsg = (m) => {
                                            try {
                                                console.debug('[ggblab] pre-warm comm.onMsg', { kernelId: kid, msg: m });
                                            }
                                            catch (ee) {
                                                /* ignore */
                                            }
                                            try {
                                                if (typeof prevOnMsg === 'function')
                                                    prevOnMsg(m);
                                            }
                                            catch (ee) {
                                                /* ignore */
                                            }
                                        };
                                    }
                                    catch (ee) {
                                        /* ignore */
                                    }
                                    try {
                                        const prevOnClose = preComm.onClose;
                                        preComm.onClose = (m) => {
                                            try {
                                                console.debug('[ggblab] pre-warm comm.onClose', { kernelId: kid, msg: m });
                                            }
                                            catch (ee) {
                                                /* ignore */
                                            }
                                            try {
                                                if (typeof prevOnClose === 'function')
                                                    prevOnClose(m);
                                            }
                                            catch (ee) {
                                                /* ignore */
                                            }
                                        };
                                    }
                                    catch (ee) {
                                        /* ignore */
                                    }
                                    try {
                                        preComm.open && preComm.open('pre-warm from ggblab');
                                    }
                                    catch (ee) {
                                        /* ignore open errors */
                                    }
                                    try {
                                        window.__ggblab_comm_store = window.__ggblab_comm_store || {};
                                        window.__ggblab_comm_store[kid] = preComm;
                                    }
                                    catch (ee) {
                                        /* ignore store errors */
                                    }
                                    try {
                                        window.__ggblab_comm_by_id = window.__ggblab_comm_by_id || {};
                                        const mid = preComm && (preComm.comm_id || preComm.commId || null);
                                        if (mid) {
                                            window.__ggblab_comm_by_id[mid] = preComm;
                                            try {
                                                window.__ggblab_comm_by_id[mid].__ggblab_meta = {
                                                    source: 'pre-warmed',
                                                    kernelId: kid,
                                                    when: new Date().toISOString()
                                                };
                                            }
                                            catch (ee) {
                                                /* ignore */
                                            }
                                            console.debug('[ggblab] pre-warmed frontend comm by id', kid, mid);
                                        }
                                        else {
                                            console.debug('[ggblab] pre-warmed frontend comm (no id yet)', kid);
                                        }
                                    }
                                    catch (ee) {
                                        console.warn('ggblab: failed to publish pre-warmed comm', ee);
                                    }
                                }
                                catch (ee) {
                                    console.warn('ggblab: failed to create pre-warm comm', kid, ee);
                                }
                            }
                        }
                        catch (ee) {
                            /* ignore pre-warm pathway errors */
                        }
                    }
                    catch (e) {
                        console.warn('ggblab: failed to register comm target for kernel', kid, e);
                    }
                };
                const km = new _jupyterlab_services__WEBPACK_IMPORTED_MODULE_5__.KernelManager({ serverSettings });
                const kmAny = km;
                if (typeof kmAny.listRunning === 'function') {
                    const list = await kmAny.listRunning();
                    console.debug('ggblab: KernelManager.listRunning returned', Array.isArray(list) ? list.length : 'non-array');
                    if (Array.isArray(list)) {
                        for (const k of list) {
                            const kid = (k && k.id) || '';
                            await registerKernel(kid, k);
                        }
                    }
                }
                else if (kmAny.running && typeof kmAny.running === 'function') {
                    console.debug('ggblab: using KernelManager.running async iterator');
                    for await (const k of kmAny.running()) {
                        try {
                            const kid = (k && k.id) || '';
                            await registerKernel(kid, k);
                        }
                        catch (e) {
                            /* ignore individual kernel errors */
                        }
                    }
                }
                // Additionally, if a serviceManager.sessions API is available use
                // session listings to detect kernels that may not yet be visible
                // through the KernelManager running list immediately after start.
                try {
                    const svc = app.serviceManager;
                    const sessAny = svc && svc.sessions;
                    if (sessAny) {
                        console.debug('ggblab: serviceManager.sessions available - scanning sessions');
                        if (typeof sessAny.listRunning === 'function') {
                            const sl = await sessAny.listRunning();
                            console.debug('ggblab: sessions.listRunning returned', Array.isArray(sl) ? sl.length : 'non-array');
                            if (Array.isArray(sl)) {
                                for (const s of sl) {
                                    try {
                                        const kmod = (s && s.kernel) || null;
                                        const kid = (kmod && kmod.id) || '';
                                        console.debug('ggblab: session entry kernel id', kid);
                                        if (kid) {
                                            await registerKernel(kid, kmod);
                                        }
                                    }
                                    catch (ee) {
                                        /* ignore per-session errors */
                                    }
                                }
                            }
                        }
                        else if (sessAny.running && typeof sessAny.running === 'function') {
                            console.debug('ggblab: using sessions.running async iterator');
                            for await (const s of sessAny.running()) {
                                try {
                                    const kmod = (s && s.kernel) || null;
                                    const kid = (kmod && kmod.id) || '';
                                    console.debug('ggblab: session stream kernel id', kid);
                                    if (kid) {
                                        await registerKernel(kid, kmod);
                                    }
                                }
                                catch (ee) {
                                    /* ignore per-session errors */
                                }
                            }
                        }
                    }
                }
                catch (ee) {
                    /* ignore serviceManager.session listing errors */
                }
                console.debug('ggblab: scanAndRegisterKernels complete');
                console.debug('ggblab: currently registered (end)', Array.from(registered));
            }
            catch (e) {
                console.warn('ggblab: KernelManager scan failed', e);
            }
        };
        // Run initial scan
        void scanAndRegisterKernels();
        // If the app exposes a serviceManager.sessions signal, re-scan when
        // running sessions change so newly-started kernels get pre-registered.
        try {
            const svc = app.serviceManager;
            if (svc) {
                // sessions.runningChanged
                if (svc.sessions && svc.sessions.runningChanged) {
                    try {
                        svc.sessions.runningChanged.connect(() => {
                            console.debug('ggblab: sessions.runningChanged — rescanning kernels');
                            void scanAndRegisterKernels();
                        });
                        console.debug('ggblab: connected sessions.runningChanged');
                    }
                    catch (e) {
                        console.warn('ggblab: failed to connect sessions.runningChanged', e);
                    }
                }
                // kernels.runningChanged (catch kernel start/stop/restart events)
                try {
                    const kv = svc.kernels;
                    if (kv && kv.runningChanged) {
                        try {
                            kv.runningChanged.connect(() => {
                                console.debug('ggblab: kernels.runningChanged — rescanning kernels');
                                void scanAndRegisterKernels();
                            });
                            console.debug('ggblab: connected kernels.runningChanged');
                        }
                        catch (e) {
                            console.warn('ggblab: failed to connect kernels.runningChanged', e);
                        }
                    }
                }
                catch (e) {
                    /* ignore kernels signal hookup errors */
                }
            }
        }
        catch (e) {
            /* non-fatal if serviceManager is absent */
        }
        // Auto-detection and wrapping of the jupyter-widgets manager removed.
        // The `widgetManager` must be supplied explicitly when creating widgets
        // (passed in `args.widgetManager`), if available in the host.
        if (settingRegistry) {
            settingRegistry
                .load(plugin.id)
                .then(settings => {
                console.debug('ggblab settings loaded:', settings.composite);
            })
                .catch(reason => {
                console.error('Failed to load settings for ggblab.', reason);
            });
        }
        const { commands } = app;
        // Tracker for created GeoGebra widgets so they can be restored after reload
        // @ts-expect-error TS2344: cross-package Lumino types can differ between
        // @jupyterlab/ui-components and @jupyterlab/apputils; ignore here and
        // prefer structural compatibility at runtime.
        const tracker = new _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.WidgetTracker({
            namespace: 'ggblab-tracker'
        });
        const command = CommandIDs.create;
        commands.addCommand(command, {
            caption: 'Create a new React Widget',
            label: 'React Widget',
            icon: args => (args['isPalette'] ? undefined : _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_3__.reactIcon),
            execute: async (args) => {
                console.debug('socketPath:', args['socketPath']);
                // Precompute widget id so we can detect and remove any existing panel
                const idPart = (args['kernelId'] || '').substring(0, 8);
                const widgetId = `ggblab-${idPart}`;
                // If a widget with the same id exists, close and remove it first.
                try {
                    const existing = tracker.find((w) => w.id === widgetId);
                    if (existing) {
                        try {
                            existing.close();
                        }
                        catch (e) {
                            console.warn('Failed to close existing widget:', e);
                        }
                        try {
                            // tracker.remove may return a Promise
                            await tracker.remove(existing);
                        }
                        catch (e) {
                            // non-fatal
                            console.warn('Failed to remove existing widget from tracker:', e);
                        }
                    }
                }
                catch (e) {
                    // If tracker API differs, ignore and continue
                }
                // WidgetManager must be provided explicitly via args if available.
                const widgetManager = args['widgetManager'] || undefined;
                // Ensure a frontend-side comm handler is registered early for the
                // requested kernel so that comm_open from the kernel will be accepted
                // even if it happens before the widget fully mounts. Store any
                // accepted comms in a global map keyed by kernel id for the widget
                // instance to consume when it mounts.
                try {
                    const baseUrl = _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_6__.PageConfig.getBaseUrl();
                    const token = _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_6__.PageConfig.getToken();
                    const settings = _jupyterlab_services__WEBPACK_IMPORTED_MODULE_5__.ServerConnection.makeSettings({
                        baseUrl,
                        token,
                        appendToken: true
                    });
                    const model = { name: 'python3', id: args['kernelId'] || '' };
                    const earlyConn = new _jupyterlab_services__WEBPACK_IMPORTED_MODULE_5__.KernelConnection({
                        model,
                        serverSettings: settings
                    });
                    // create global store if missing
                    window.__ggblab_comm_store =
                        window.__ggblab_comm_store || {};
                    const store = window.__ggblab_comm_store;
                    // Register a no-op handler that saves the comm object for later use
                    earlyConn.registerCommTarget(args['commTarget'] || 'ggblab-comm', (commOp, msg) => {
                        try {
                            store[args['kernelId']] = commOp;
                            console.debug('Registered early frontend comm for kernel', args['kernelId']);
                        }
                        catch (e) {
                            console.warn('Failed to store early frontend comm', e);
                        }
                    });
                }
                catch (e) {
                    console.warn('Failed to register early frontend comm target', e);
                }
                const content = new _widget__WEBPACK_IMPORTED_MODULE_4__.GeoGebraWidget({
                    kernelId: args['kernelId'] || '',
                    commTarget: args['commTarget'] || 'ggblab-comm',
                    insertMode: args['insertMode'] || 'split-right',
                    socketPath: args['socketPath'] || '',
                    wsPort: args['wsPort'] || 8888,
                    widgetManager: widgetManager
                });
                // @ts-expect-error TS2344: cross-package Lumino types can differ between
                // @jupyterlab/ui-components and @jupyterlab/apputils; ignore here and
                // prefer structural compatibility at runtime.
                const widget = new _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_1__.MainAreaWidget({ content });
                // make widget id unique so restorer can identify it later
                widget.id = widgetId;
                widget.title.label = `GeoGebra (${idPart})`;
                widget.title.icon = _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_3__.reactIcon;
                // register with tracker so state will be saved for restoration
                try {
                    await tracker.add(widget);
                }
                catch (e) {
                    console.warn('Failed to add widget to tracker:', e);
                }
                app.shell.add(widget, 'main', {
                    mode: args['insertMode'] || 'split-right'
                });
            }
        });
        // palette.addItem({
        //   command,
        //   category: "Tutorial",
        // });
        if (restorer) {
            // Note: we may in future support restoring the applet's internal
            // state from an autosave (e.g. localStorage or a persistent store).
            // That would involve fetching a saved XML/Base64 snapshot and
            // passing it through `args` or a dedicated `initialXml` prop so the
            // recreated widget can rehydrate the GeoGebra applet.
            restorer.restore(tracker, {
                command,
                // use widget.id as the saved name so it is unique per widget
                name: widget => widget.id,
                // reconstruct args (kernelId) from the saved widget id so the
                // command can recreate the widget with the same kernel association
                args: widget => {
                    // Prefer to read the original creation props from the widget content
                    const content = (widget && widget.content) || {};
                    const p = content.props || {};
                    // Fallback to reconstructing kernelId from the widget id if not present
                    const id = widget.id || '';
                    const kernelId = p.kernelId ||
                        (id.startsWith('ggblab-') ? id.slice('ggblab-'.length) : '');
                    return {
                        kernelId,
                        commTarget: p.commTarget || '',
                        socketPath: p.socketPath || '',
                        wsPort: p.wsPort || 8888,
                        insertMode: p.insertMode || 'split-right'
                    };
                }
            });
        }
        // Launcher integration removed: no launcher item will be added.
    }
};
// Export the main plugin only.
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (plugin);


/***/ },

/***/ "./lib/widget.js"
/*!***********************!*\
  !*** ./lib/widget.js ***!
  \***********************/
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   GeoGebraWidget: () => (/* binding */ GeoGebraWidget)
/* harmony export */ });
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyterlab/ui-components */ "webpack/sharing/consume/default/@jupyterlab/ui-components");
/* harmony import */ var _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! react */ "webpack/sharing/consume/default/react");
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _jupyterlab_services__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @jupyterlab/services */ "webpack/sharing/consume/default/@jupyterlab/services");
/* harmony import */ var _jupyterlab_services__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_services__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @jupyterlab/coreutils */ "webpack/sharing/consume/default/@jupyterlab/coreutils");
/* harmony import */ var _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_3__);


//import MetaTags from 'react-meta-tags';


// Global typings are provided in src/declarations.d.ts; avoid duplicate declarations here.
// Debug logging helper controlled from the browser console.
// Enable message logging in the JS console by running:
//   window.ggblabDebugMessages = true
function dbg(...args) {
    if (window.ggblabDebugMessages) {
        // eslint-disable-next-line no-console
        console.log(...args);
    }
}
/**
 * React component for a GeoGebra.
 *
 * @returns The React component
 */
const GGAComponent = (props) => {
    // const [kernels, setKernels] = React.useState<any[]>([]);
    const widgetRef = (0,react__WEBPACK_IMPORTED_MODULE_1__.useRef)(null);
    // const [size, setSize] = useState<{width: number; height: number}>({width: 800, height: 600});
    // The following `useState` + resize-listener is intentionally commented out.
    // Lumino's layout and `onResize` handling are the primary resize signals
    // for this widget; the code is kept as a reference for future experiments
    // (ResizeObserver and alternate strategies were unreliable across themes).
    // // Listen to resize events to update size state
    // // but not working as expected in Lumino
    //   useEffect(() => {
    //     window.addEventListener('resize', () => {
    //     if (widgetRef.current) {
    //         setSize({
    //             width: widgetRef.current.offsetWidth,
    //             height: widgetRef.current.offsetHeight,
    //         });
    //         console.log("Resized to:", size.width, size.height);
    //     }
    //     });
    //   }, []);
    // Normalize kernelId early to avoid undefined issues when props are missing
    const kernelId = (props === null || props === void 0 ? void 0 : props.kernelId) || '';
    dbg('Component props: ', kernelId, props.commTarget, props.socketPath, props.wsPort);
    const elementId = 'ggb-element-' + kernelId.substring(0, 8);
    dbg('Element ID:', elementId);
    let applet = null;
    // Prefer a widget manager explicitly passed via props. Global manager
    // registration has been removed; do not attempt to read `window.__ggblab_widget_manager`.
    const effectiveWidgetManager = props.widgetManager;
    dbg('effectiveWidgetManager resolved:', !!effectiveWidgetManager, {
        kernelId
    });
    function isArrayOfArrays(value) {
        return (Array.isArray(value) && value.every(subArray => Array.isArray(subArray)));
    }
    /**
     * Calls a remote procedure on kernel2 to send a message via remote socket between kernel2 to kernel.
     * Executes Python code on kernel2 that sends the message through either a unix socket or websocket.
     *
     * Note on WebSocket Connection Handling:
     * Previous attempts to maintain persistent websocket connections using ping/pong (keep-alive)
     * were unsuccessful. Websocket connections established via kernel2.requestExecute() execute
     * within isolated contexts that are torn down immediately after the code execution completes.
     * Even with ping/pong mechanisms, connections would be disconnected once the kernel's
     * requestExecute() context ended. Therefore, the implementation creates new socket connections
     * for each message send operation, which is more reliable than attempting to maintain
     * persistent but fragile connections.
     *
     * @param kernel2 - The kernel to execute the remote procedure on
     * @param message - The message to send (as a JSON string)
     * @param socketPath - Optional unix socket path (if provided, uses unix socket; otherwise uses websocket)
     * @param wsUrl - WebSocket URL (used if socketPath is not provided)
     */
    // Serialize outgoing socket sends to avoid kernel-side requestExecute jams.
    // `sendChain` is a promise chain that ensures each send completes before
    // the next begins. We also add a small inter-send delay to give the
    // remote helper kernel time to tear down connections.
    let sendChain = Promise.resolve();
    async function callRemoteSocketSend(kernel2, message, socketPath, wsUrl) {
        try {
            dbg('callRemoteSocketSend: sending message', {
                socketPath,
                wsUrl,
                messagePreview: message.slice(0, 200)
            });
            // Queue the actual send work on the chain so sends are serialized.
            const doSend = async () => {
                if (socketPath) {
                    await kernel2.requestExecute({
                        code: `
with unix_connect("${socketPath}") as ws:
    ws.send(r"""${message}""")
`
                    }).done;
                }
                else {
                    await kernel2.requestExecute({
                        code: `
with connect("${wsUrl}") as ws:
    ws.send(r"""${message}""")
`
                    }).done;
                }
                await new Promise(resolve => setTimeout(resolve, 30));
            };
            // Append to chain and ensure errors don't break future sends.
            const next = sendChain.then(() => doSend());
            // swallow errors on chain so chain remains healthy
            sendChain = next.catch(() => {
                /* ignore errors to keep chain alive */
            });
            await next;
            try {
                dbg('callRemoteSocketSend: sent', { idPreview: message.slice(0, 40) });
            }
            catch (e) {
                /* ignore */
            }
        }
        catch (err) {
            try {
                console.error('callRemoteSocketSend: error sending message', err);
            }
            catch (e) {
                /* ignore */
            }
            throw err;
        }
    }
    (0,react__WEBPACK_IMPORTED_MODULE_1__.useEffect)(() => {
        // No global widget-manager events are used now.
        // Track resources created during effect so we can clean them up precisely
        let kernel2 = null;
        let kernelManager = null;
        let kernelConn = null;
        let comm = null;
        // Reserved for future ipywidgets-based bridge (kept intentionally).
        // When enabled, `widgetComm` will be assigned to a frontend-managed
        // widget comm to allow in-kernel widgets to be routed directly to
        // the GeoGebra instance without using the remote socket.
        let widgetComm = null;
        let managerAdopted = false;
        const registeredKernelTargets = [];
        let appletApi = null;
        let observer = null;
        let resizeHandler = null;
        let closeHandler = null;
        let metaViewport = null;
        let scriptTag = null;
        (async () => {
            return await _jupyterlab_services__WEBPACK_IMPORTED_MODULE_2__.KernelAPI.listRunning();
        })().then(async (kernels) => {
            // setKernels(kernels);
            dbg('Running kernels:', kernels);
            const baseUrl = _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_3__.PageConfig.getBaseUrl();
            const token = _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_3__.PageConfig.getToken();
            dbg(`Base URL: ${baseUrl}`);
            dbg(`Token: ${token}`);
            const settings = _jupyterlab_services__WEBPACK_IMPORTED_MODULE_2__.ServerConnection.makeSettings({
                baseUrl: baseUrl, //'http://localhost:8889/',
                token: token, //'7e89be30eb93ee7c149a839d4c7577e08c2c25b3c7f14647',
                appendToken: true
            });
            kernelManager = new _jupyterlab_services__WEBPACK_IMPORTED_MODULE_2__.KernelManager({ serverSettings: settings });
            kernel2 = await kernelManager.startNew({ name: 'python3' });
            dbg('Started new kernel:', kernel2, kernelId);
            await kernel2.requestExecute({
                code: 'from websockets.sync.client import unix_connect, connect'
            }).done;
            const wsUrl = `ws://localhost:${props.wsPort}/`;
            const socketPath = props.socketPath || null;
            // Try an early out-of-band probe so the kernel may mark the
            // helper-server channel as ready for same-cell replies. This is
            // a fire-and-forget probe executed on the helper kernel (`kernel2`).
            try {
                const probeMsg = JSON.stringify({ type: 'probe', payload: 'ready' });
                // fire-and-forget the probe so we don't block the widget mount
                callRemoteSocketSend(kernel2, probeMsg, socketPath, wsUrl).catch((e) => dbg('probe send failed', e));
                dbg('Sent early OOB probe via helper kernel');
                // Also send an explicit oob_ready signal so the kernel can
                // mark the out-of-band channel as ready for same-cell replies.
                try {
                    const readyMsg = JSON.stringify({
                        type: 'oob_ready',
                        payload: 'frontend'
                    });
                    callRemoteSocketSend(kernel2, readyMsg, socketPath, wsUrl).catch((e) => dbg('oob_ready send failed', e));
                    dbg('Sent explicit oob_ready via helper kernel');
                }
                catch (e) {
                    dbg('Failed to schedule oob_ready send', e);
                }
            }
            catch (e) {
                dbg('Failed to schedule early OOB probe', e);
            }
            kernelConn = new _jupyterlab_services__WEBPACK_IMPORTED_MODULE_2__.KernelConnection({
                model: { name: 'python3', id: kernelId || kernels[0]['id'] },
                serverSettings: settings
            });
            dbg('Connected to kernel:', kernelConn);
            // Keep comm lifecycle state and helpers for recovery when comms close
            let commClosed = false;
            const attachCommCloseHandler = (c) => {
                try {
                    c.onClose = (m) => {
                        try {
                            commClosed = true;
                            const closedId = (m && m.content && m.content.comm_id) ||
                                (c === null || c === void 0 ? void 0 : c.comm_id) ||
                                (c === null || c === void 0 ? void 0 : c.commId) ||
                                null;
                            dbg('Kernel comm closed', {
                                target: props.commTarget,
                                commId: closedId,
                                message: m
                            });
                        }
                        catch (e) {
                            dbg('Kernel comm closed (no id available)', props.commTarget, m);
                        }
                        try {
                            // cleanup global stores when this comm closes
                            let cid = null;
                            try {
                                cid = (m && m.content && m.content.comm_id) || (c === null || c === void 0 ? void 0 : c.comm_id) || (c === null || c === void 0 ? void 0 : c.commId) || null;
                                if (cid && window.__ggblab_comm_by_id) {
                                    try {
                                        delete window.__ggblab_comm_by_id[cid];
                                    }
                                    catch (ee) {
                                        /* ignore */
                                    }
                                }
                            }
                            catch (ee) {
                                /* ignore */
                            }
                            try {
                                const sk = kernelId || (kernelConn === null || kernelConn === void 0 ? void 0 : kernelConn.id) || null;
                                if (sk && window.__ggblab_comm_store) {
                                    try {
                                        const cur = window.__ggblab_comm_store[sk];
                                        if (cur === c) {
                                            delete window.__ggblab_comm_store[sk];
                                            dbg('Removed comm from __ggblab_comm_store on close', sk, cid);
                                        }
                                    }
                                    catch (ee) {
                                        /* ignore */
                                    }
                                }
                            }
                            catch (ee) {
                                /* ignore */
                            }
                        }
                        catch (ee) {
                            /* ignore cleanup errors */
                        }
                    };
                }
                catch (e) {
                    dbg('Unable to attach onClose to kernel comm', e);
                }
            };
            // Centralized processing of a parsed command and sending replies.
            // `sourceComm` is optional and, when provided, will be used to
            // send the reply. Otherwise we fall back to the kernel-side `comm`
            // or the remote socket.
            const processCommand = async (command, sourceComm) => {
                try {
                    dbg('processCommand:', command === null || command === void 0 ? void 0 : command.type, command === null || command === void 0 ? void 0 : command.payload);
                    let rmsg = null;
                    if (!appletApi) {
                        dbg('Applet API not ready; cannot service command');
                        return;
                    }
                    if (command.type === 'command') {
                        const label = appletApi.evalCommandGetLabels(command.payload);
                        rmsg = JSON.stringify({
                            type: 'created',
                            id: command.id,
                            payload: label
                        });
                    }
                    else if (command.type === 'function') {
                        const apiName = command.payload.name;
                        const args = command.payload.args;
                        let value = [];
                        (Array.isArray(apiName) ? apiName : [apiName]).forEach((f) => {
                            if (isArrayOfArrays(args)) {
                                const v2 = [];
                                args.forEach((a) => {
                                    v2.push(appletApi[f](...a) || null);
                                });
                                value.push(v2);
                            }
                            else {
                                value.push(args
                                    ? appletApi[f](...args) || null
                                    : appletApi[f]() || null);
                            }
                        });
                        value = Array.isArray(apiName) ? value : value[0];
                        rmsg = JSON.stringify({
                            type: 'value',
                            id: command.id,
                            payload: { value }
                        });
                    }
                    if (!rmsg) {
                        return;
                    }
                    // Prefer replying on the source comm (widget-manager comm)
                    // if provided. Next prefer the kernel-created comm. Fallback
                    // to callRemoteSocketSend.
                    try {
                        if (sourceComm && typeof sourceComm.send === 'function') {
                            try {
                                sourceComm.send(rmsg);
                                dbg('Replied via sourceComm');
                            }
                            catch (e) {
                                dbg('sourceComm.send failed', e);
                                throw e;
                            }
                            return;
                        }
                    }
                    catch (e) {
                        dbg('Error sending via sourceComm', e);
                    }
                    try {
                        if (!comm || commClosed) {
                            await ensureKernelComm();
                        }
                        if (comm && typeof comm.send === 'function') {
                            try {
                                comm.send(rmsg);
                                dbg('Replied via kernel comm');
                                return;
                            }
                            catch (e) {
                                dbg('kernel comm.send failed', e);
                                try {
                                    dbg('Fallback: send failed, forwarding to remote socket');
                                    await callRemoteSocketSend(kernel2, rmsg, socketPath, wsUrl);
                                    dbg('Fallback: forwarded to remote socket');
                                }
                                catch (ee) {
                                    dbg('Fallback remote socket send failed', ee);
                                }
                                // Attempt to re-warm a frontend comm on failure and retry
                                try {
                                    if (kernelConn && typeof kernelConn.createComm === 'function') {
                                        try {
                                            const newComm = kernelConn.createComm(props.commTarget);
                                            try {
                                                newComm.onMsg = handleIncomingCommMessage;
                                            }
                                            catch (ee) {
                                                /* ignore */
                                            }
                                            attachCommCloseHandler(newComm);
                                            try {
                                                newComm.open && newComm.open('re-warm from ggblab');
                                            }
                                            catch (ee) {
                                                /* ignore */
                                            }
                                            try {
                                                window.__ggblab_comm_store = window.__ggblab_comm_store || {};
                                                const sk = kernelId || (kernelConn === null || kernelConn === void 0 ? void 0 : kernelConn.id) || null;
                                                if (sk)
                                                    window.__ggblab_comm_store[sk] = newComm;
                                            }
                                            catch (ee) {
                                                /* ignore */
                                            }
                                            try {
                                                window.__ggblab_comm_by_id = window.__ggblab_comm_by_id || {};
                                                const mid = newComm && (newComm.comm_id || newComm.commId || null);
                                                if (mid) {
                                                    window.__ggblab_comm_by_id[mid] = newComm;
                                                    try {
                                                        window.__ggblab_comm_by_id[mid].__ggblab_meta = {
                                                            source: 're-warmed',
                                                            kernelId: kernelId || (kernelConn === null || kernelConn === void 0 ? void 0 : kernelConn.id) || null,
                                                            when: new Date().toISOString()
                                                        };
                                                    }
                                                    catch (ee) {
                                                        /* ignore */
                                                    }
                                                }
                                            }
                                            catch (ee) {
                                                /* ignore */
                                            }
                                            // replace comm reference and retry send
                                            comm = newComm;
                                            commClosed = false;
                                            try {
                                                comm.send(rmsg);
                                                dbg('Replied via re-warmed comm');
                                                return;
                                            }
                                            catch (ee) {
                                                dbg('re-warmed comm send failed', ee);
                                            }
                                        }
                                        catch (ee) {
                                            dbg('Failed to re-warm comm', ee);
                                        }
                                    }
                                }
                                catch (ee) {
                                    dbg('Re-warm attempt failed', ee);
                                }
                            }
                        }
                    }
                    catch (e) {
                        dbg('Error sending via kernel comm', e);
                    }
                    // Last resort: mirror to remote socket
                    try {
                        await callRemoteSocketSend(kernel2, rmsg, socketPath, wsUrl);
                        dbg('Replied via remote socket');
                    }
                    catch (e) {
                        dbg('Failed to reply via remote socket', e);
                    }
                }
                catch (e) {
                    dbg('processCommand error', e);
                }
            };
            // Handler for incoming messages on the kernel-created comm; defined
            // once so it can be reattached if we recreate the comm. This assumes
            // kernel comm messages place the command JSON in `msg.content.data`.
            const handleIncomingCommMessage = async (msg) => {
                var _a;
                dbg('handleIncomingCommMessage:', msg);
                try {
                    const data = ((_a = msg === null || msg === void 0 ? void 0 : msg.content) === null || _a === void 0 ? void 0 : _a.data) || msg;
                    const command = typeof data === 'string' ? JSON.parse(data) : data;
                    await processCommand(command, /* sourceComm */ comm);
                }
                catch (e) {
                    dbg('Error in handleIncomingCommMessage', e);
                }
            };
            // Ensure a kernel comm exists; create and attach handlers if missing.
            const ensureKernelComm = async () => {
                if (comm && !commClosed) {
                    return comm;
                }
                try {
                    // If an early frontend-side comm was registered (plugin activation)
                    // reuse it. This allows comm_open from the kernel to be accepted
                    // before the widget fully mounts.
                    let pre = null;
                    try {
                        const store = window.__ggblab_comm_store || {};
                        // Prefer any comm in the by-id map that was tagged for this kernelId
                        try {
                            const byId = window.__ggblab_comm_by_id || {};
                            const lookupKeyForById = kernelId || (kernelConn === null || kernelConn === void 0 ? void 0 : kernelConn.id) || '';
                            let firstNoMeta = null;
                            const byIdKeys = Object.keys(byId || {});
                            if (lookupKeyForById) {
                                for (const k in byId) {
                                    try {
                                        const candidate = byId[k];
                                        const meta = candidate && (candidate.__ggblab_meta || {});
                                        if (meta && meta.kernelId) {
                                            const mid = meta.kernelId;
                                            const matches = mid === lookupKeyForById ||
                                                (lookupKeyForById && mid.startsWith(lookupKeyForById)) ||
                                                (mid && lookupKeyForById && lookupKeyForById.startsWith(mid));
                                            if (matches) {
                                                pre = candidate;
                                                dbg('Found pre-registered comm by by_id map', k, lookupKeyForById, meta && meta.source, 'meta.kernelId=', mid);
                                                break;
                                            }
                                        }
                                        // remember first candidate that lacks meta for fallback
                                        if (!meta && !firstNoMeta) {
                                            firstNoMeta = candidate;
                                        }
                                    }
                                    catch (ee) {
                                        /* ignore per-entry errors */
                                    }
                                }
                            }
                            // Fallback: if no meta-based match found but there is exactly
                            // one by-id entry, accept it as the pre-registered comm. This
                            // is a pragmatic fallback for older builds that didn't attach
                            // meta; prefer explicit meta matches when available.
                            try {
                                if (!pre && !firstNoMeta && byIdKeys.length === 1) {
                                    firstNoMeta = byId[byIdKeys[0]];
                                }
                                if (!pre && firstNoMeta && byIdKeys.length === 1) {
                                    pre = firstNoMeta;
                                    dbg('Using sole by-id candidate without meta as fallback', byIdKeys[0]);
                                }
                            }
                            catch (ee) {
                                /* ignore fallback errors */
                            }
                        }
                        catch (ee) {
                            /* ignore by-id lookup errors */
                        }
                        // Prefer an explicit kernelId passed via props. If missing,
                        // fallback to the id exposed by the connected kernelConn so
                        // that widgets that omitted `kernelId` still reuse pre-registered
                        // comms created during plugin activation.
                        const lookupKey = kernelId || (kernelConn === null || kernelConn === void 0 ? void 0 : kernelConn.id) || '';
                        // Try exact key first; if not found, allow prefix matches so
                        // short kernelId values (e.g. "269127d0") match full UUID keys.
                        let storeKey = lookupKey;
                        if (lookupKey && !store[lookupKey]) {
                            for (const sk in store) {
                                try {
                                    if (sk.startsWith(lookupKey) || lookupKey.startsWith(sk)) {
                                        storeKey = sk;
                                        dbg('Mapped lookupKey to store key', lookupKey, '->', sk);
                                        break;
                                    }
                                }
                                catch (ee) {
                                    /* ignore */
                                }
                            }
                        }
                        if (storeKey && store[storeKey]) {
                            pre = store[storeKey];
                        }
                        else if (lookupKey) {
                            // If no direct store entry, check for queued comm-open messages
                            try {
                                const qstore = window.__ggblab_comm_queue || {};
                                const q = qstore[lookupKey] || [];
                                if (q && q.length) {
                                    // Attempt to extract a comm id from the queued message
                                    const m0 = q.shift();
                                    try {
                                        const maybeCommId = (m0 && m0.content && m0.content.comm_id) ||
                                            (m0 && m0.comm_id) ||
                                            null;
                                        if (maybeCommId) {
                                            const byId = window.__ggblab_comm_by_id || {};
                                            if (byId[maybeCommId]) {
                                                pre = byId[maybeCommId];
                                                dbg('Found pre-registered comm by commId from queue', maybeCommId);
                                                // update the queue store after shifting
                                                window.__ggblab_comm_queue[lookupKey] = q;
                                            }
                                        }
                                    }
                                    catch (ee) {
                                        /* ignore parsing errors */
                                    }
                                }
                            }
                            catch (ee) {
                                /* ignore queue errors */
                            }
                        }
                        if (pre) {
                            comm = pre;
                            try {
                                comm.onMsg = handleIncomingCommMessage;
                            }
                            catch (e) {
                                dbg('Failed to attach onMsg to pre-registered comm', e);
                            }
                            attachCommCloseHandler(comm);
                            commClosed = false;
                            dbg('Using pre-registered frontend comm for kernel', kernelId || kernelConn.id);
                            try {
                                window.__ggblab_comm_by_id = window.__ggblab_comm_by_id || {};
                                const maybeId = (comm === null || comm === void 0 ? void 0 : comm.comm_id) || (comm === null || comm === void 0 ? void 0 : comm.commId) || null;
                                if (maybeId) {
                                    window.__ggblab_comm_by_id[maybeId] = comm;
                                    window.__ggblab_comm_by_id[maybeId].__ggblab_meta = {
                                        source: 'pre-registered',
                                        kernelId: kernelId || (kernelConn === null || kernelConn === void 0 ? void 0 : kernelConn.id) || null,
                                        when: new Date().toISOString()
                                    };
                                    dbg('Marked comm as pre-registered', maybeId);
                                }
                            }
                            catch (e) {
                                dbg('Failed to mark pre-registered comm by id', e);
                            }
                            try {
                                // Visible, persistent console output for timing/debugging
                                // eslint-disable-next-line no-console
                                console.log('[ggblab] using pre-registered comm', {
                                    when: new Date().toISOString(),
                                    lookupKey: kernelId || kernelConn.id,
                                    commId: (comm === null || comm === void 0 ? void 0 : comm.comm_id) || (comm === null || comm === void 0 ? void 0 : comm.commId) || null
                                });
                            }
                            catch (e) {
                                /* ignore logging errors */
                            }
                            return comm;
                        }
                    }
                    catch (e) {
                        dbg('Error checking pre-registered comm store', e);
                    }
                    // If no pre-registered comm found yet, wait briefly for one to arrive
                    // (mitigates race where comm_open arrives just after we check).
                    if (!pre) {
                        try {
                            dbg('No pre-registered comm found — waiting briefly for arrival');
                            const waitForPre = async (timeout = 2000, interval = 50) => {
                                const end = Date.now() + timeout;
                                const lookupKey = kernelId || (kernelConn === null || kernelConn === void 0 ? void 0 : kernelConn.id) || '';
                                while (Date.now() < end) {
                                    // check by-id map
                                    try {
                                        const byId = window.__ggblab_comm_by_id || {};
                                        if (lookupKey) {
                                            for (const k in byId) {
                                                try {
                                                    const candidate = byId[k];
                                                    const meta = candidate && (candidate.__ggblab_meta || {});
                                                    if (meta && meta.kernelId) {
                                                        const mid = meta.kernelId;
                                                        const matches = mid === lookupKey ||
                                                            (lookupKey && mid.startsWith(lookupKey)) ||
                                                            (mid && lookupKey && lookupKey.startsWith(mid));
                                                        if (matches) {
                                                            dbg('waitForPre: found by-id', k, 'meta.kernelId=', mid);
                                                            return byId[k];
                                                        }
                                                    }
                                                }
                                                catch (ee) {
                                                    /* ignore */
                                                }
                                            }
                                        }
                                    }
                                    catch (ee) {
                                        /* ignore */
                                    }
                                    // check store
                                    try {
                                        const store2 = window.__ggblab_comm_store || {};
                                        if (lookupKey && store2[lookupKey]) {
                                            dbg('waitForPre: found in store', lookupKey);
                                            return store2[lookupKey];
                                        }
                                        // allow prefix matches for short kernel ids
                                        if (lookupKey) {
                                            for (const sk in store2) {
                                                try {
                                                    if (sk.startsWith(lookupKey) || lookupKey.startsWith(sk)) {
                                                        dbg('waitForPre: found in store by prefix', lookupKey, '->', sk);
                                                        return store2[sk];
                                                    }
                                                }
                                                catch (ee) {
                                                    /* ignore */
                                                }
                                            }
                                        }
                                    }
                                    catch (ee) {
                                        /* ignore */
                                    }
                                    // check queue
                                    try {
                                        const qstore = window.__ggblab_comm_queue || {};
                                        const q = lookupKey ? qstore[lookupKey] || [] : [];
                                        if (q && q.length) {
                                            const m0 = q[0];
                                            const maybeCommId = (m0 && m0.content && m0.content.comm_id) || (m0 && m0.comm_id) || null;
                                            if (maybeCommId) {
                                                const byId2 = window.__ggblab_comm_by_id || {};
                                                if (byId2[maybeCommId]) {
                                                    dbg('waitForPre: found byId from queue', maybeCommId);
                                                    return byId2[maybeCommId];
                                                }
                                            }
                                        }
                                    }
                                    catch (ee) {
                                        /* ignore */
                                    }
                                    await new Promise(r => setTimeout(r, interval));
                                }
                                return null;
                            };
                            const arrived = await waitForPre(2000, 50);
                            if (arrived) {
                                pre = arrived;
                                dbg('Pre-registered comm arrived during wait');
                            }
                            else {
                                dbg('No pre-registered comm arrived within wait period');
                                try {
                                    if (window.ggblabDebugMessages) {
                                        // Verbose dump for debugging old/new frontend mismatch
                                        try {
                                            // eslint-disable-next-line no-console
                                            console.log('[ggblab] debug dump: __ggblab_comm_store keys', Object.keys(window.__ggblab_comm_store || {}));
                                            // eslint-disable-next-line no-console
                                            console.log('[ggblab] debug dump: __ggblab_comm_by_id keys', Object.keys(window.__ggblab_comm_by_id || {}));
                                            const byId = window.__ggblab_comm_by_id || {};
                                            for (const k of Object.keys(byId)) {
                                                try {
                                                    // eslint-disable-next-line no-console
                                                    console.log('[ggblab] debug dump: by_id entry', k, byId[k] && byId[k].__ggblab_meta);
                                                }
                                                catch (ee) {
                                                    /* ignore */
                                                }
                                            }
                                        }
                                        catch (ee) {
                                            /* ignore debug dump errors */
                                        }
                                    }
                                }
                                catch (ee) {
                                    /* ignore */
                                }
                            }
                        }
                        catch (ee) {
                            /* ignore wait errors */
                        }
                    }
                    // If no pre-registered comm arrived, do not create a fallback
                    // comm here. Removing the recreate fallback simplifies reasoning
                    // and ensures widgets only reuse frontend-accepted comms.
                    if (!pre) {
                        dbg('No pre-registered comm available; skipping recreate fallback');
                        return null;
                    }
                }
                catch (e) {
                    dbg('ensureKernelComm failed', e);
                    return null;
                }
            };
            // Register handlers to accept widget-model comms created by the kernel's
            // ipywidgets machinery. When the kernel creates a widget (e.g. IntSlider)
            // it will open a comm to the frontend with target 'jupyter.widget'
            // (and sometimes 'jupyter.widget.control'). We register a simple
            // passthrough handler only when no widgetManager is present; if a
            // widgetManager is available we must not intercept those comms.
            try {
                // Small delay to give any late-arriving manager passed via props
                await new Promise(res => setTimeout(res, 120));
                const lateMgr = props.widgetManager;
                if (lateMgr) {
                    dbg('Widget manager provided via props; skipping passthrough registration');
                }
                else {
                    dbg('No widget manager provided; registering passthrough comm targets');
                    const registerTarget = (target) => {
                        try {
                            if (registeredKernelTargets.includes(target)) {
                                dbg('Skipping duplicate registration for target', target);
                                return;
                            }
                            kernelConn.registerCommTarget(target, (c, msg) => {
                                try {
                                    dbg('Accepted comm open for target', target, { msg });
                                    try {
                                        c.onMsg = handleIncomingCommMessage;
                                    }
                                    catch (e) {
                                        dbg('Failed to attach onMsg to incoming comm', e);
                                    }
                                    attachCommCloseHandler(c);
                                    comm = c;
                                    try {
                                        window.__ggblab_comm_by_id = window.__ggblab_comm_by_id || {};
                                        const cid = (c && (c.comm_id || c.commId)) || null;
                                        if (cid) {
                                            window.__ggblab_comm_by_id[cid] = c;
                                            window.__ggblab_comm_by_id[cid].__ggblab_meta = {
                                                source: 'accepted-target',
                                                target,
                                                kernelId: (props === null || props === void 0 ? void 0 : props.kernelId) || (kernelConn === null || kernelConn === void 0 ? void 0 : kernelConn.id) || null,
                                                when: new Date().toISOString()
                                            };
                                            dbg('Marked accepted incoming comm', cid, target);
                                        }
                                    }
                                    catch (e) {
                                        dbg('Failed to mark accepted incoming comm', e);
                                    }
                                    try {
                                        // eslint-disable-next-line no-console
                                        console.log('[ggblab] accepted comm open', {
                                            when: new Date().toISOString(),
                                            target,
                                            kernelId: (props === null || props === void 0 ? void 0 : props.kernelId) || (kernelConn === null || kernelConn === void 0 ? void 0 : kernelConn.id) || null,
                                            msg
                                        });
                                    }
                                    catch (e) {
                                        /* ignore */
                                    }
                                }
                                catch (e) {
                                    dbg('Error handling incoming comm open', e);
                                }
                            });
                            registeredKernelTargets.push(target);
                            dbg('Registered comm target', target);
                        }
                        catch (e) {
                            dbg('Failed to register comm target', target, e);
                        }
                    };
                    // Register common widget manager targets and the ggblab-specific target
                    // try { registerTarget('jupyter.widget.control'); } catch (e) { /* ignore */ }
                    try {
                        registerTarget(props.commTarget || 'ggblab-comm');
                    }
                    catch (e) {
                        /* ignore */
                    }
                }
            }
            catch (e) {
                dbg('Widget comm target registration skipped or failed', e);
            }
            // Adopt a WidgetManager if/when it appears at runtime.
            const adoptWidgetManager = (mgr) => {
                var _a, _b;
                try {
                    if (!mgr) {
                        return;
                    }
                    if (managerAdopted) {
                        return;
                    }
                    const commManager = (mgr === null || mgr === void 0 ? void 0 : mgr.comm_manager) ||
                        (mgr === null || mgr === void 0 ? void 0 : mgr.commManager) ||
                        (mgr === null || mgr === void 0 ? void 0 : mgr._commManager) ||
                        ((_a = mgr === null || mgr === void 0 ? void 0 : mgr._manager) === null || _a === void 0 ? void 0 : _a.comm_manager) ||
                        ((_b = mgr === null || mgr === void 0 ? void 0 : mgr._kernel) === null || _b === void 0 ? void 0 : _b.comm_manager) ||
                        null;
                    if (!commManager ||
                        typeof commManager.register_target !== 'function') {
                        dbg('adoptWidgetManager: no comm_manager available on manager', !!commManager);
                        return;
                    }
                    managerAdopted = true;
                    dbg('Adopting widget manager; registering targets on commManager');
                    const attachHandler = (commOp, msg, sourceName) => {
                        dbg('manager adapter: comm opened', sourceName, commOp, msg);
                        try {
                            widgetComm = commOp;
                            const handler = async (m) => {
                                var _a;
                                const data = ((_a = m === null || m === void 0 ? void 0 : m.content) === null || _a === void 0 ? void 0 : _a.data) || m;
                                const command = typeof data === 'string' ? JSON.parse(data) : data;
                                await processCommand(command, widgetComm);
                            };
                            try {
                                if (typeof commOp.on_msg === 'function') {
                                    commOp.on_msg(handler);
                                }
                                else if (typeof commOp.onMsg === 'function') {
                                    commOp.onMsg = handler;
                                }
                                else if (typeof commOp.on === 'function') {
                                    commOp.on('msg', handler);
                                }
                                else if ('on_msg' in commOp) {
                                    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
                                    // @ts-ignore
                                    commOp.on_msg = handler;
                                }
                                else {
                                    try {
                                        commOp.onMsg = handler;
                                    }
                                    catch (e) {
                                        dbg('Unable to attach handler to commOp', e);
                                    }
                                }
                            }
                            catch (e) {
                                dbg('Failed to attach message handler to manager-provided comm', e);
                            }
                        }
                        catch (e) {
                            dbg('Error in manager adapter comm handler', e);
                        }
                    };
                    const tryRegister = (mgr, t) => {
                        try {
                            if (typeof mgr.register_target === 'function') {
                                mgr.register_target(t, (commOp, msg) => attachHandler(commOp, msg, t));
                                dbg('commManager.register_target succeeded for', t);
                                return true;
                            }
                            if (typeof mgr.registerTarget === 'function') {
                                mgr.registerTarget(t, (commOp, msg) => attachHandler(commOp, msg, t));
                                dbg('commManager.registerTarget succeeded for', t);
                                return true;
                            }
                            if (typeof mgr.register === 'function') {
                                mgr.register(t, (commOp, msg) => attachHandler(commOp, msg, t));
                                dbg('commManager.register succeeded for', t);
                                return true;
                            }
                            dbg('commManager has no known register API for target', t);
                            return false;
                        }
                        catch (e) {
                            dbg('Failed to register target on commManager', t, e);
                            return false;
                        }
                    };
                    const targetsToRegister = [props.commTarget || 'ggblab-comm', 'jupyter.widget', 'jupyter.widget.control'];
                    for (const t of targetsToRegister) {
                        tryRegister(commManager, t);
                    }
                    // Publish the adopted manager to a global store so other mounts
                    // can adopt the same manager if they mount later.
                    try {
                        window.__ggblab_widget_manager = window.__ggblab_widget_manager || {};
                        const key = (props === null || props === void 0 ? void 0 : props.kernelId) || (kernelConn === null || kernelConn === void 0 ? void 0 : kernelConn.id) || 'last';
                        window.__ggblab_widget_manager[key] = mgr;
                        window.__ggblab_widget_manager['last'] = mgr;
                        try {
                            window.dispatchEvent(new CustomEvent('ggblab:widget-manager-registered'));
                            dbg('Dispatched ggblab:widget-manager-registered');
                        }
                        catch (ee) {
                            dbg('Failed to dispatch ggblab:widget-manager-registered', ee);
                        }
                    }
                    catch (ee) {
                        dbg('Failed to publish widget manager to global store', ee);
                    }
                    // Attempt to remove kernelConn passthrough targets if possible
                    try {
                        if (kernelConn && kernelConn.removeCommTarget) {
                            registeredKernelTargets.forEach(t => {
                                try {
                                    kernelConn.removeCommTarget(t);
                                    dbg('Removed kernelConn target', t);
                                }
                                catch (e) {
                                    /* ignore */
                                }
                            });
                        }
                    }
                    catch (e) {
                        dbg('Error while removing kernelConn targets', e);
                    }
                }
                catch (e) {
                    dbg('adoptWidgetManager error', e);
                }
            };
            const onGlobalManager = () => {
                try {
                    // If a specific comm target was provided by the kernel, do
                    // not adopt a manager from the global store — the kernel
                    // explicitly requested the comm target and we should avoid
                    // overriding that decision.
                    if (props === null || props === void 0 ? void 0 : props.commTarget) {
                        dbg('props.commTarget present; skipping adoptWidgetManager');
                        return;
                    }
                    const store = window.__ggblab_widget_manager || {};
                    if ((props === null || props === void 0 ? void 0 : props.kernelId) && store[props.kernelId]) {
                        return adoptWidgetManager(store[props.kernelId]);
                    }
                    const keys = Object.keys(store || {});
                    if (keys.length) {
                        return adoptWidgetManager(store['last'] || store[keys[0]]);
                    }
                }
                catch (e) {
                    dbg('onGlobalManager error', e);
                }
            };
            window.addEventListener('ggblab:widget-manager-registered', onGlobalManager);
            // If a manager was already present at mount, adopt immediately
            try {
                if (effectiveWidgetManager) {
                    adoptWidgetManager(effectiveWidgetManager);
                }
            }
            catch (e) {
                dbg('Immediate adopt failed', e);
            }
            async function ggbOnLoad(api) {
                dbg('GeoGebra applet loaded:', api);
                // expose applet API to other handlers (widgetComm etc.)
                appletApi = api;
                // "start" is unnecessary because the frontend emits an
                // explicit "oob_ready" when the applet loads; kernel-side
                // logic should treat that as the readiness/start signal.
                resizeHandler = function () {
                    const wrapperDiv = document.getElementById(elementId);
                    const parentDiv = wrapperDiv === null || wrapperDiv === void 0 ? void 0 : wrapperDiv.parentElement;
                    const width = parseInt((parentDiv === null || parentDiv === void 0 ? void 0 : parentDiv.style.width) || '800');
                    const height = parseInt((parentDiv === null || parentDiv === void 0 ? void 0 : parentDiv.style.height) || '600');
                    api.recalculateEnvironments();
                    api.setSize(width, height);
                };
                window.addEventListener('resize', resizeHandler);
                resizeHandler();
                // Create kernel-side Comm now that the applet is initialized.
                // Use the shared helper `ensureKernelComm()` so we reuse the
                // same creation / attach logic (and avoid duplicating open/handler setup).
                if (props.commTarget) {
                    try {
                        // Request the main kernel to register the requested comm target
                        // into a persistent instance so the kernel will accept the
                        // frontend's `createComm` open. Use a module-level
                        // `ggb_comm_instance` to keep the instance alive.
                        try {
                            const regCode = `from ggblab.comm import ggb_comm\nif 'ggb_comm_instance' not in globals():\n    ggb_comm_instance = ggb_comm()\nggb_comm_instance.register_target("${props.commTarget}")\n`;
                            await kernelConn.requestExecute({ code: regCode }).done;
                        }
                        catch (e) {
                            dbg('Failed to request kernel to register comm target', e);
                        }
                        const maybeComm = await ensureKernelComm();
                        if (maybeComm) {
                            comm = maybeComm;
                            try {
                                const maybeId = (comm === null || comm === void 0 ? void 0 : comm.comm_id) ||
                                    (comm === null || comm === void 0 ? void 0 : comm.commId) ||
                                    (comm === null || comm === void 0 ? void 0 : comm.id) ||
                                    null;
                                dbg('Created kernel comm via ensureKernelComm', {
                                    target: props.commTarget,
                                    commObject: comm,
                                    commId: maybeId
                                });
                            }
                            catch (e) {
                                dbg('Created kernel comm via ensureKernelComm (unable to read id)', props.commTarget, comm);
                            }
                        }
                        else {
                            comm = null;
                            dbg('ensureKernelComm returned null; skipping kernel comm creation');
                        }
                    }
                    catch (e) {
                        comm = null;
                        dbg('ensureKernelComm failed; skipping kernel comm creation', e);
                    }
                }
                else {
                    comm = null;
                    dbg('No commTarget provided; skipping kernel comm creation');
                }
                // // Observe size changes of the widget's DOM element
                // // but not working as expected in Lumino
                // const widgetElemnt = window.document.querySelector('div.lm-DockPanel-widget');
                // const widgetElemnt = window.document.querySelector('div.lm-SplitPanel-child');
                // const widgetElemnt = window.document.querySelector('div[class*="Panel"]');
                // if (widgetElemnt) {
                // if (widgetRef.current) {
                //     const resizeObserver = new ResizeObserver(() => {
                //         console.log("Panel resized.");
                //         resize();
                //     });
                //     resizeObserver.observe(widgetRef.current); //widgetElemnt);
                // }
                // Defer kernel-side Comm creation until the applet is loaded.
                // The comm will be created inside `ggbOnLoad` to ensure the
                // applet exists before we attempt to wire kernel↔frontend comms.
                // comm.send('HELO2').done
                // kernel.registerCommTarget('test', (comm, commMsg) => {
                // console.log("Comm opened from kernel with message:", commMsg['content']['data']);
                closeHandler = () => {
                    var _a;
                    // Attempt to close comm and shutdown helper kernel
                    try {
                        (_a = comm === null || comm === void 0 ? void 0 : comm.close) === null || _a === void 0 ? void 0 : _a.call(comm);
                    }
                    catch (e) {
                        console.error(e);
                    }
                    kernel2 === null || kernel2 === void 0 ? void 0 : kernel2.shutdown().catch((err) => console.error(err));
                    dbg('Kernel and comm closed.');
                    if (resizeHandler) {
                        window.removeEventListener('resize', resizeHandler);
                    }
                };
                window.addEventListener('close', closeHandler);
                if (comm) {
                    try {
                        comm.onMsg = handleIncomingCommMessage;
                    }
                    catch (e) {
                        dbg('Failed to attach handleIncomingCommMessage to comm', e);
                    }
                }
                else {
                    dbg('No kernel comm available; messages will be sent via remote socket only');
                }
                const addListener = async function (data) {
                    dbg('Add listener triggered for:', data);
                    const msg = {
                        type: 'add',
                        payload: data
                    };
                    // console.log("Add detected:", JSON.stringify(msg));
                    // Prefer to send via widget comm bridge if available
                    const s = JSON.stringify(msg);
                    if (widgetComm) {
                        try {
                            widgetComm.send(s);
                            return;
                        }
                        catch (e) {
                            dbg('widgetComm.send failed, falling back', e);
                        }
                    }
                    await callRemoteSocketSend(kernel2, s, socketPath, wsUrl);
                };
                api.registerAddListener(addListener);
                const removeListener = async function (data) {
                    dbg('Remove listener triggered for:', data);
                    const msg = {
                        type: 'remove',
                        payload: data
                    };
                    // console.log("Remove detected:", JSON.stringify(msg));
                    const s = JSON.stringify(msg);
                    if (widgetComm) {
                        try {
                            widgetComm.send(s);
                            return;
                        }
                        catch (e) {
                            dbg('widgetComm.send failed, falling back', e);
                        }
                    }
                    await callRemoteSocketSend(kernel2, s, socketPath, wsUrl);
                };
                api.registerRemoveListener(removeListener);
                const renameListener = async function (data) {
                    dbg('Rename listener triggered for:', data);
                    const msg = {
                        type: 'rename',
                        payload: data
                    };
                    // console.log("Rename detected:", JSON.stringify(msg));
                    const s = JSON.stringify(msg);
                    if (widgetComm) {
                        try {
                            widgetComm.send(s);
                            return;
                        }
                        catch (e) {
                            dbg('widgetComm.send failed, falling back', e);
                        }
                    }
                    await callRemoteSocketSend(kernel2, s, socketPath, wsUrl);
                };
                api.registerRenameListener(renameListener);
                const clearListener = async function (data) {
                    dbg('Clear listener triggered for:', data);
                    const msg = {
                        type: 'clear',
                        payload: data
                    };
                    // console.log("Rename detected:", JSON.stringify(msg));
                    const s = JSON.stringify(msg);
                    if (widgetComm) {
                        try {
                            widgetComm.send(s);
                            return;
                        }
                        catch (e) {
                            dbg('widgetComm.send failed, falling back', e);
                        }
                    }
                    await callRemoteSocketSend(kernel2, s, socketPath, wsUrl);
                };
                api.registerClearListener(clearListener);
                // The `clientListener` example below is kept commented out as a
                // reference for future event types. It's disabled because it
                // was not used in production and could generate noisy traffic.
                // // nothing triggered?
                // var clientListener = async function(data: any) {
                // // console.log("Add listener triggered for:", data);
                //     var msg = {
                //         "type": "client",
                //         "payload": data
                //     }
                //     console.log("Client detected:", JSON.stringify(msg));
                //     await callRemoteSocketSend(kernel2, JSON.stringify(msg), socketPath, wsUrl);
                // }
                // api.registerClearListener(clientListener);
                observer = new MutationObserver(mutations => {
                    mutations.forEach(mutation => {
                        mutation.addedNodes.forEach(node => {
                            try {
                                node
                                    .querySelectorAll('div.dialogMainPanel > div.dialogTitle')
                                    .forEach(n => {
                                    dbg(n.textContent); // detect titles like 'Error'
                                    node.querySelector('div.dialogContent')
                                        .querySelectorAll("[class$='Label']")
                                        .forEach(async (n2) => {
                                        dbg(n2.textContent);
                                        const msg = JSON.stringify({
                                            type: n.textContent,
                                            payload: n2.textContent
                                        });
                                        // comm.send(msg);
                                        await callRemoteSocketSend(kernel2, msg, socketPath, wsUrl);
                                    });
                                });
                            }
                            catch (e) {
                                // console.log(e, node);
                            }
                        });
                    });
                });
                observer.observe(document.body, { childList: true, subtree: true });
            }
            // Avoid duplicate meta/script inserts: reuse if already present
            const existingMeta = document.getElementById('ggblab-viewport-meta');
            if (existingMeta) {
                metaViewport = existingMeta;
            }
            else {
                metaViewport = document.createElement('meta');
                metaViewport.id = 'ggblab-viewport-meta';
                metaViewport.name = 'viewport';
                metaViewport.content = 'width=device-width, initial-scale=1';
                document.head.appendChild(metaViewport);
            }
            const existingScript = document.getElementById('ggblab-deployggb-script');
            const createApplet = () => {
                const params = {
                    id: 'ggbApplet' + ((props === null || props === void 0 ? void 0 : props.kernelId) || '').substring(0, 8), // applet ID
                    appName: 'suite', // specify GeoGebra Classic smart applet
                    width: 800, // applet width
                    height: 600, // applet height
                    showToolBar: true, // show the toolbar
                    showAlgebraInput: false, // show algebra input field
                    showMenuBar: true, // show the menu bar
                    autoHeight: true,
                    scaleContainerClass: 'lm-Panel', // "lm-DockPanel-widget",
                    // autoWidth: false,
                    // scale: 2,
                    allowUpscale: false,
                    appletOnLoad: ggbOnLoad
                };
                applet = new window.GGBApplet(params, true);
                applet.inject(elementId);
                // Expose the active applet instance on `window.ggbApplet` for
                // consistency across the codebase and for debug tooling.
                try {
                    window.ggbApplet = applet;
                }
                catch (e) {
                    /* ignore */
                }
            };
            if (existingScript) {
                scriptTag = existingScript;
                // If script already loaded and GGBApplet is available, instantiate immediately
                if (window.GGBApplet) {
                    createApplet();
                }
                else {
                    // Otherwise ensure we call createApplet once it loads
                    scriptTag.addEventListener('load', createApplet, { once: true });
                }
            }
            else {
                scriptTag = document.createElement('script');
                scriptTag.id = 'ggblab-deployggb-script';
                scriptTag.src = 'https://cdn.geogebra.org/apps/deployggb.js';
                scriptTag.async = true;
                scriptTag.onload = createApplet;
                document.body.appendChild(scriptTag);
            }
        });
        return () => {
            // Remove resize listener
            if (resizeHandler) {
                window.removeEventListener('resize', resizeHandler);
                resizeHandler = null;
            }
            // Remove close listener
            if (closeHandler) {
                window.removeEventListener('close', closeHandler);
                closeHandler = null;
            }
            // Disconnect mutation observer
            if (observer) {
                try {
                    observer.disconnect();
                }
                catch (e) {
                    console.error(e);
                }
                observer = null;
            }
            // Remove injected meta tag
            if (metaViewport && metaViewport.parentNode) {
                metaViewport.parentNode.removeChild(metaViewport);
                metaViewport = null;
            }
            // Remove injected script tag
            if (scriptTag && scriptTag.parentNode) {
                scriptTag.parentNode.removeChild(scriptTag);
                scriptTag = null;
            }
            // Clean up GeoGebra applet
            if (applet) {
                try {
                    dbg('Cleaning up GeoGebra applet.');
                    // Use the unified `window.ggbApplet` reference when available
                    const winApplet = window.ggbApplet || applet;
                    try {
                        winApplet.remove();
                    }
                    catch (e) {
                        dbg('Error removing applet instance', e);
                    }
                }
                catch (e) {
                    dbg('Error while removing GeoGebra applet', e);
                }
                applet = null;
                try {
                    delete window.ggbApplet;
                }
                catch (e) {
                    console.debug('ggblab: ignored', e);
                }
            }
            // Close comm and shutdown helper kernel asynchronously
            (async () => {
                var _a, _b;
                try {
                    if (comm) {
                        try {
                            (_a = comm.close) === null || _a === void 0 ? void 0 : _a.call(comm);
                        }
                        catch (e) {
                            dbg('Error closing comm during cleanup', e);
                        }
                        comm = null;
                    }
                    if (kernel2) {
                        await kernel2.shutdown();
                        kernel2 = null;
                    }
                    // Clear any widget comm bridge reference
                    try {
                        widgetComm = null;
                    }
                    catch (e) {
                        /* ignore */
                    }
                    try {
                        appletApi = null;
                    }
                    catch (e) {
                        /* ignore */
                    }
                    if (kernelManager) {
                        try {
                            await ((_b = kernelManager.shutdown) === null || _b === void 0 ? void 0 : _b.call(kernelManager));
                        }
                        catch (e) {
                            /* ignore */
                        }
                        kernelManager = null;
                    }
                }
                catch (e) {
                    console.error('Error during cleanup:', e);
                }
            })();
        };
    }, []);
    return (react__WEBPACK_IMPORTED_MODULE_1___default().createElement("div", { id: elementId, ref: widgetRef, style: { width: '100%', height: '100%' } }));
};
/**
 * A GeoGebra Lumino Widget that wraps a GeoGebraComponent.
 */
class GeoGebraWidget extends _jupyterlab_ui_components__WEBPACK_IMPORTED_MODULE_0__.ReactWidget {
    /**
     * Constructs a new GeoGebraWidget.
     */
    constructor(props) {
        super();
        this.addClass('jp-ggblabWidget');
        this.props = props || {};
        // Ensure a sensible default comm target so frontend and kernel
        // consistently use the same channel when callers omit it.
        this.props.commTarget = this.props.commTarget || 'ggblab-comm';
    }
    render() {
        var _a, _b, _c, _d, _e;
        return (react__WEBPACK_IMPORTED_MODULE_1___default().createElement(GGAComponent, { kernelId: (_a = this.props) === null || _a === void 0 ? void 0 : _a.kernelId, commTarget: (_b = this.props) === null || _b === void 0 ? void 0 : _b.commTarget, wsPort: (_c = this.props) === null || _c === void 0 ? void 0 : _c.wsPort, socketPath: (_d = this.props) === null || _d === void 0 ? void 0 : _d.socketPath, widgetManager: (_e = this.props) === null || _e === void 0 ? void 0 : _e.widgetManager }));
    }
    // only onResize is responsible for size changes in Lumino,
    // but onAfterAttach and onAfterShow and onFitRequest may also be relevant in some cases.
    onResize(msg) {
        // console.log("GeoGebraWidget resized:", msg.width, msg.height);
        window.dispatchEvent(new Event('resize'));
        super.onResize(msg);
    }
    // Only perform cleanup when the widget is explicitly closed by the user.
    // Use onCloseRequest to trigger cleanup so that transient disposals
    // during layout/restore operations do not tear down the internal state.
    onCloseRequest(msg) {
        dbg('GeoGebraWidget onCloseRequest — performing cleanup.');
        window.dispatchEvent(new Event('close'));
        super.onCloseRequest(msg);
    }
    // dispose should not trigger cleanup again; allow normal disposal to proceed
    // without duplicating shutdown logic.
    dispose() {
        dbg('GeoGebraWidget disposed.');
        super.dispose();
    }
}
// // Example of attaching the GeoGebraWidget to a DockPanel
// // but commented out to avoid automatic execution.
// const dock = new DockPanel();
// ReactWidget.attach(dock, document.body);
// // window.addEventListener('resize', () => { dock.update(); });
// dock.layoutModified.connect(() => {
//     console.log("Dock layout modified.");
//     dock.update();
// });


/***/ },

/***/ "./package.json"
/*!**********************!*\
  !*** ./package.json ***!
  \**********************/
(module) {

module.exports = /*#__PURE__*/JSON.parse('{"name":"ggblab","version":"1.2.1","description":"A JupyterLab extension for learning geometry and Python programming side-by-side with GeoGebra.","keywords":["jupyter","jupyterlab","jupyterlab-extension"],"homepage":"https://github.com/moyhig-ecs/ggblab#readme","bugs":{"url":"https://github.com/moyhig-ecs/ggblab/issues"},"license":"BSD-3-Clause","author":{"name":"Manabu Higashida","email":"manabu@higashida.net"},"files":["lib/**/*.{d.ts,eot,gif,html,jpg,js,js.map,json,png,svg,woff2,ttf}","style/**/*.{css,js,eot,gif,html,jpg,json,png,svg,woff2,ttf}","src/**/*.{ts,tsx}","schema/*.json"],"main":"lib/index.js","types":"lib/index.d.ts","style":"style/index.css","repository":{"type":"git","url":"https://github.com/moyhig-ecs/ggblab"},"scripts":{"build":"jlpm build:lib && jlpm build:labextension:dev","build:prod":"jlpm clean && jlpm build:lib:prod && jlpm build:labextension","build:labextension":"jupyter labextension build .","build:labextension:dev":"jupyter labextension build --development True .","build:lib":"tsc --sourceMap","build:lib:prod":"tsc","clean":"jlpm clean:lib","clean:lib":"rimraf lib tsconfig.tsbuildinfo","clean:lintcache":"rimraf .eslintcache .stylelintcache","clean:labextension":"rimraf ggblab/labextension ggblab/_version.py","clean:all":"jlpm clean:lib && jlpm clean:labextension && jlpm clean:lintcache","eslint":"jlpm eslint:check --fix","eslint:check":"eslint . --cache --ext .ts,.tsx","install:extension":"jlpm build","lint":"jlpm stylelint && jlpm prettier && jlpm eslint","lint:check":"jlpm stylelint:check && jlpm prettier:check && jlpm eslint:check","prettier":"jlpm prettier:base --write --list-different","prettier:base":"prettier \\"**/*{.ts,.tsx,.js,.jsx,.css,.json,.md}\\"","prettier:check":"jlpm prettier:base --check","stylelint":"jlpm stylelint:check --fix","stylelint:check":"stylelint --cache \\"style/**/*.css\\"","test":"jest --coverage","watch":"run-p watch:src watch:labextension","watch:src":"tsc -w --sourceMap","watch:labextension":"jupyter labextension watch ."},"dependencies":{"@jupyter-widgets/base":"^4.0.0","@jupyter-widgets/jupyterlab-manager":"^5.0.15","@jupyterlab/application":"^4.0.0","@jupyterlab/apputils":"^4.6.1","@jupyterlab/launcher":"^4.5.1","@jupyterlab/settingregistry":"^4.0.0","@lumino/widgets":"^2.7.2","@marshallku/react-postscribe":"^0.2.0","react-meta-tags":"^1.0.1"},"devDependencies":{"@jupyterlab/builder":"^4.0.0","@jupyterlab/testutils":"^4.0.0","@types/jest":"^29.2.0","@types/json-schema":"^7.0.11","@types/react":"^18.0.26","@types/react-addons-linked-state-mixin":"^0.14.22","@typescript-eslint/eslint-plugin":"^6.1.0","@typescript-eslint/parser":"^6.1.0","css-loader":"^6.7.1","eslint":"^8.36.0","eslint-config-prettier":"^8.8.0","eslint-plugin-prettier":"^5.0.0","jest":"^29.2.0","npm-run-all2":"^7.0.1","prettier":"^3.0.0","rimraf":"^5.0.1","source-map-loader":"^1.0.2","style-loader":"^3.3.1","stylelint":"^15.10.1","stylelint-config-recommended":"^13.0.0","stylelint-config-standard":"^34.0.0","stylelint-csstree-validator":"^3.0.0","stylelint-prettier":"^4.0.0","typescript":"~5.5.4","yjs":"^13.5.0"},"resolutions":{"lib0":"0.2.111"},"sideEffects":["style/*.css","style/index.js"],"styleModule":"style/index.js","publishConfig":{"access":"public"},"jupyterlab":{"extension":true,"outputDir":"ggblab/labextension","schemaDir":"schema"},"eslintIgnore":["node_modules","dist","coverage","**/*.d.ts","tests","**/__tests__","ui-tests"],"eslintConfig":{"extends":["eslint:recommended","plugin:@typescript-eslint/eslint-recommended","plugin:@typescript-eslint/recommended","plugin:prettier/recommended"],"parser":"@typescript-eslint/parser","parserOptions":{"project":"tsconfig.json","sourceType":"module"},"plugins":["@typescript-eslint"],"rules":{"@typescript-eslint/naming-convention":["error",{"selector":"interface","format":["PascalCase"],"custom":{"regex":"^I[A-Z]","match":true}}],"@typescript-eslint/no-unused-vars":["warn",{"args":"none"}],"@typescript-eslint/no-explicit-any":"off","@typescript-eslint/no-namespace":"off","@typescript-eslint/no-use-before-define":"off","@typescript-eslint/quotes":["error","single",{"avoidEscape":true,"allowTemplateLiterals":false}],"curly":["error","all"],"eqeqeq":"error","prefer-arrow-callback":"error"}},"prettier":{"singleQuote":true,"trailingComma":"none","arrowParens":"avoid","endOfLine":"auto","overrides":[{"files":"package.json","options":{"tabWidth":4}}]},"stylelint":{"extends":["stylelint-config-recommended","stylelint-config-standard","stylelint-prettier/recommended"],"plugins":["stylelint-csstree-validator"],"rules":{"csstree/validator":true,"property-no-vendor-prefix":null,"selector-class-pattern":"^([a-z][A-z\\\\d]*)(-[A-z\\\\d]+)*$","selector-no-vendor-prefix":null,"value-no-vendor-prefix":null}}}');

/***/ }

}]);
//# sourceMappingURL=lib_index_js.7cb834d6d87dd17c1583.js.map