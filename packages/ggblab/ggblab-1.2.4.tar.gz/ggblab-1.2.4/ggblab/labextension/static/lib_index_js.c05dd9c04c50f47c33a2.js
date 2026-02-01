"use strict";
(self["webpackChunkggblab"] = self["webpackChunkggblab"] || []).push([["lib_index_js"],{

/***/ "./lib/index.js"
/*!**********************!*\
  !*** ./lib/index.js ***!
  \**********************/
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   createWidgetManagerLegacy: () => (/* binding */ createWidgetManagerLegacy),
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
/* harmony import */ var _widgetManager__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./widgetManager */ "./lib/widgetManager.js");
/* harmony import */ var _package_json__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ../package.json */ "./package.json");


// ILauncher removed: launcher integration is not used in this build

//import { DockLayout } from '@lumino/widgets';



/**
 * Legacy/compatibility note:
 * Historically the plugin created a `widgetManager` inline in this
 * module during activation. The implementation has been moved to
 * `src/widgetManager.ts` to centralize widget-manager logic and to
 * allow different manager implementations (or `undefined`) to be
 * swapped in. We keep a tiny forwarding helper here as a documented
 * placeholder so future maintainers can see the original intent and
 * have a single place to adapt call-sites if needed.
 */
function createWidgetManagerLegacy() {
    // Forward to the real factory in widgetManager.ts for now.
    return (0,_widgetManager__WEBPACK_IMPORTED_MODULE_5__.createWidgetManager)();
}
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
        console.debug(`JupyterLab extension ggblab-${_package_json__WEBPACK_IMPORTED_MODULE_6__.version} is activated!`);
        // Pragmatic global registration (option B): register a `jupyter.ggblab`
        // comm target on all currently running kernels so kernels that open
        // comms to that target will be delivered to the front-end. Keep the
        // returned unregister function so we can clean up on unload.
        let _unregisterGlobalGGBlab = null;
        (0,_widgetManager__WEBPACK_IMPORTED_MODULE_5__.registerGlobalGGBlabCommTargets)(app)
            .then(unreg => {
            _unregisterGlobalGGBlab = unreg;
        })
            .catch(e => console.warn('Failed to register global ggblab comm targets', e));
        // Ensure we clean up registrations when the page unloads to avoid
        // leaving dangling front-end KernelConnection objects.
        window.addEventListener('beforeunload', () => {
            try {
                _unregisterGlobalGGBlab === null || _unregisterGlobalGGBlab === void 0 ? void 0 : _unregisterGlobalGGBlab();
            }
            catch (e) {
                /* ignore */
            }
        });
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
                // Centralized widget-manager factory (currently returns `undefined`)
                // to avoid interfering with ipywidgets. See src/widgetManager.ts
                // for future changes to this behavior.
                const widgetManager = (0,_widgetManager__WEBPACK_IMPORTED_MODULE_5__.createWidgetManager)();
                const content = new _widget__WEBPACK_IMPORTED_MODULE_4__.GeoGebraWidget({
                    kernelId: args['kernelId'] || '',
                    commTarget: args['commTarget'] || '',
                    insertMode: args['insertMode'] || 'split-right',
                    socketPath: args['socketPath'] || '',
                    wsPort: args['wsPort'] || 8888,
                    widgetManager: widgetManager
                });
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
/* harmony import */ var _widgetManager__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./widgetManager */ "./lib/widgetManager.js");


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
    dbg('Component props: ', props.kernelId, props.commTarget, props.socketPath, props.wsPort);
    // window.dispatchEvent(new Event('resize'));
    const elementId = 'ggb-element-' + ((props === null || props === void 0 ? void 0 : props.kernelId) || '').substring(0, 8);
    dbg('Element ID:', elementId);
    let applet = null;
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
                // small delay to give the helper kernel a moment to tear down
                // and to avoid immediate back-to-back requestExecute calls.
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
        let appletApi = null;
        let _unregisterWidgetComms = null;
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
            dbg('Started new kernel:', kernel2, props.kernelId);
            await kernel2.requestExecute({
                code: 'from websockets.sync.client import unix_connect, connect'
            }).done;
            const wsUrl = `ws://localhost:${props.wsPort}/`;
            const socketPath = props.socketPath || null;
            kernelConn = new _jupyterlab_services__WEBPACK_IMPORTED_MODULE_2__.KernelConnection({
                model: { name: 'python3', id: props.kernelId || kernels[0]['id'] },
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
                    };
                }
                catch (e) {
                    dbg('Unable to attach onClose to kernel comm', e);
                }
            };
            // Handler for incoming messages on the kernel-created comm; defined
            // once so it can be reattached if we recreate the comm.
            const handleIncomingCommMessage = async (msg) => {
                dbg('handleIncomingCommMessage:', msg);
                try {
                    dbg('Kernel comm onMsg received', {
                        commTarget: props.commTarget,
                        msg
                    });
                    const command = JSON.parse(msg.content.data);
                    dbg('Parsed command:', command.type, command.payload);
                    let rmsg = null;
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
                        dbg('apiName:', apiName);
                        let value = [];
                        {
                            const args = command.payload.args;
                            value = [];
                            (Array.isArray(apiName) ? apiName : [apiName]).forEach((f) => {
                                dbg('call', f, args);
                                if (isArrayOfArrays(args)) {
                                    const value2 = [];
                                    args.forEach((arg2) => {
                                        if (args) {
                                            value2.push(appletApi[f](...arg2) || null);
                                        }
                                        else {
                                            value2.push(appletApi[f]() || null);
                                        }
                                    });
                                    value.push(value2);
                                }
                                else {
                                    if (args) {
                                        value.push(appletApi[f](...args) || null);
                                    }
                                    else {
                                        value.push(appletApi[f]() || null);
                                    }
                                }
                            });
                            value = Array.isArray(apiName) ? value : value[0];
                            dbg('Function value:', value);
                        }
                        rmsg = JSON.stringify({
                            type: 'value',
                            id: command.id,
                            payload: { value: value }
                        });
                    }
                    // Try to send via kernel comm; if that fails, mirror to remote socket.
                    try {
                        try {
                            const cId = (comm === null || comm === void 0 ? void 0 : comm.comm_id) || (comm === null || comm === void 0 ? void 0 : comm.commId) || null;
                            dbg('Sending via kernel comm', {
                                commTarget: props.commTarget,
                                commId: cId,
                                preview: (rmsg || '').slice(0, 200)
                            });
                        }
                        catch (e) {
                            /* ignore */
                        }
                        // If comm is closed or missing, attempt to recreate before send
                        if (!comm || commClosed) {
                            try {
                                await ensureKernelComm();
                            }
                            catch (e) {
                                dbg('ensureKernelComm failed before sending reply', e);
                            }
                        }
                        if (comm) {
                            comm.send(rmsg);
                        }
                        else {
                            dbg('No kernel comm available to send reply; will mirror via remote socket');
                        }
                    }
                    catch (e) {
                        dbg('Failed to send via kernel comm, will still attempt remote socket send', e, { rmsgPreview: (rmsg || '').slice(0, 200) });
                    }
                    await callRemoteSocketSend(kernel2, rmsg, socketPath, wsUrl);
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
                    if (!kernelConn) {
                        throw new Error('No kernelConn available to create comm');
                    }
                    comm = kernelConn.createComm(props.commTarget);
                    try {
                        const maybeId = (comm === null || comm === void 0 ? void 0 : comm.comm_id) ||
                            (comm === null || comm === void 0 ? void 0 : comm.commId) ||
                            (comm === null || comm === void 0 ? void 0 : comm.id) ||
                            null;
                        dbg('Recreated kernel comm', {
                            target: props.commTarget,
                            commObject: comm,
                            commId: maybeId
                        });
                    }
                    catch (e) {
                        dbg('Recreated kernel comm (unable to read id)', props.commTarget, comm);
                    }
                    // attach handlers
                    try {
                        comm.onMsg = handleIncomingCommMessage;
                    }
                    catch (e) {
                        dbg('Failed to attach onMsg to recreated comm', e);
                    }
                    attachCommCloseHandler(comm);
                    // open the comm
                    try {
                        comm.open('REOPEN from GGB').done;
                    }
                    catch (e) {
                        dbg('Failed to open recreated comm', e);
                    }
                    commClosed = false;
                    return comm;
                }
                catch (e) {
                    dbg('ensureKernelComm failed', e);
                    return null;
                }
            };
            // Register simple passthrough handlers for jupyter.widget when no
            // widgetManager is present. The helper returns a cleanup function.
            try {
                if (props.widgetManager) {
                    dbg('widgetManager present; skipping raw jupyter.widget comm registration to avoid stealing widget opens');
                }
                else {
                    _unregisterWidgetComms = (0,_widgetManager__WEBPACK_IMPORTED_MODULE_4__.registerWidgetCommTargets)(kernelConn, {
                        callRemoteSocketSend,
                        kernel2,
                        socketPath,
                        wsUrl,
                        getAppletApi: () => appletApi,
                        isArrayOfArrays,
                        dbg
                    });
                }
            }
            catch (e) {
                dbg('Widget comm target registration skipped or failed', e);
            }
            async function ggbOnLoad(api) {
                dbg('GeoGebra applet loaded:', api);
                // expose applet API to other handlers (widgetComm etc.)
                appletApi = api;
                (async function () {
                    const msg = {
                        type: 'start',
                        payload: {}
                    };
                    await callRemoteSocketSend(kernel2, JSON.stringify(msg), socketPath, wsUrl);
                })();
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
                if (props.commTarget) {
                    comm = kernelConn.createComm(props.commTarget);
                    try {
                        // Log comm creation details for debugging 'Comm not found' issues
                        try {
                            const maybeId = (comm === null || comm === void 0 ? void 0 : comm.comm_id) ||
                                (comm === null || comm === void 0 ? void 0 : comm.commId) ||
                                (comm === null || comm === void 0 ? void 0 : comm.id) ||
                                null;
                            dbg('Created kernel comm', {
                                target: props.commTarget,
                                commObject: comm,
                                commId: maybeId
                            });
                        }
                        catch (e) {
                            dbg('Created kernel comm (unable to read id)', props.commTarget, comm);
                        }
                        comm.open('HELO from GGB').done;
                    }
                    catch (e) {
                        dbg('Failed to open kernel comm for', props.commTarget, e);
                    }
                    // Attach close handler to surface unexpected closes
                    try {
                        comm.onClose = (m) => {
                            try {
                                const closedId = (m && m.content && m.content.comm_id) ||
                                    (comm === null || comm === void 0 ? void 0 : comm.comm_id) ||
                                    (comm === null || comm === void 0 ? void 0 : comm.commId) ||
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
                        };
                    }
                    catch (e) {
                        dbg('Unable to attach onClose to kernel comm', e);
                    }
                }
                else {
                    // No kernel-level comm target provided: rely on remote socket
                    comm = null;
                    dbg('No commTarget provided; skipping kernel comm creation');
                }
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
            // Unregister widget comm handlers if we registered them
            try {
                _unregisterWidgetComms === null || _unregisterWidgetComms === void 0 ? void 0 : _unregisterWidgetComms();
                _unregisterWidgetComms = null;
            }
            catch (e) {
                dbg('Error unregistering widget comm targets', e);
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
                    /* ignore */
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
        this.props = props;
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

/***/ "./lib/widgetManager.js"
/*!******************************!*\
  !*** ./lib/widgetManager.js ***!
  \******************************/
(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   ENABLE_RUNNING_CHANGED: () => (/* binding */ ENABLE_RUNNING_CHANGED),
/* harmony export */   createWidgetManager: () => (/* binding */ createWidgetManager),
/* harmony export */   registerGlobalGGBlabCommTargets: () => (/* binding */ registerGlobalGGBlabCommTargets),
/* harmony export */   registerWidgetCommTargets: () => (/* binding */ registerWidgetCommTargets)
/* harmony export */ });
/* harmony import */ var _jupyterlab_services__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyterlab/services */ "webpack/sharing/consume/default/@jupyterlab/services");
/* harmony import */ var _jupyterlab_services__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_services__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @jupyterlab/coreutils */ "webpack/sharing/consume/default/@jupyterlab/coreutils");
/* harmony import */ var _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_1__);
// Minimal widget-manager adapter extracted from plugin/widget code.
// This module centralizes how a frontend WidgetManager (ipywidgets bridge)
// would be created or provided. For now we intentionally return `undefined`
// to preserve the previous behavior (avoiding ipywidgets interference).
/**
 * Create or obtain a WidgetManager instance.
 *
 * Note: The ggblab extension currently avoids providing a WidgetManager
 * to GeoGebra widgets by default to prevent stealing comms from
 * ipywidgets. Keep the factory here so the decision and implementation
 * can be changed in one place in future.
 */
function createWidgetManager() {
    // Intentionally return undefined to match previous behavior in
    // `src/index.ts` where `widgetManager` was left as `undefined`.
    return undefined;
}
/**
 * Register simple passthrough handlers for `jupyter.widget` and
 * `jupyter.widget.control` on the given `kernelConn` when no
 * `widgetManager` is present.
 *
 * Returns a cleanup function that will attempt to unregister the
 * comm targets when called.
 */
function registerWidgetCommTargets(kernelConn, opts) {
    // Feature flag: enable/disable the raw `jupyter.widget` passthrough
    // registration. When false (default) we skip registering handlers to
    // avoid stealing comm targets from a proper ipywidgets manager which
    // would otherwise render widget models (avoids "widget model not found").
    const ENABLE_WIDGET_COMM_PASSTHROUGH = false;
    if (!ENABLE_WIDGET_COMM_PASSTHROUGH) {
        opts.dbg && opts.dbg('Widget comm passthrough disabled by flag');
        return () => {
            /* noop unregister */
        };
    }
    const dbg = opts.dbg || (() => { });
    const simpleHandler = (commOp, msg) => {
        dbg('widget comm opened (jupyter.widget)', commOp, msg);
        try {
            commOp.onMsg = async (m) => {
                var _a;
                const content = ((_a = m === null || m === void 0 ? void 0 : m.content) === null || _a === void 0 ? void 0 : _a.data) || m;
                try {
                    const command = typeof content === 'string' ? JSON.parse(content) : content;
                    let rmsg = null;
                    const appletApi = opts.getAppletApi();
                    if (command.type === 'command' && appletApi) {
                        const label = appletApi.evalCommandGetLabels(command.payload);
                        rmsg = JSON.stringify({
                            type: 'created',
                            id: command.id,
                            payload: label
                        });
                    }
                    else if (command.type === 'function' && appletApi) {
                        const apiName = command.payload.name;
                        const args = command.payload.args;
                        let value = [];
                        (Array.isArray(apiName) ? apiName : [apiName]).forEach((f) => {
                            if (opts.isArrayOfArrays(args)) {
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
                    if (rmsg) {
                        try {
                            commOp.send(rmsg);
                        }
                        catch (e) {
                            dbg('commOp.send failed', e);
                        }
                        try {
                            await opts.callRemoteSocketSend(opts.kernel2, rmsg, opts.socketPath, opts.wsUrl);
                        }
                        catch (e) {
                            dbg('callRemoteSocketSend failed', e);
                        }
                    }
                }
                catch (e) {
                    dbg('Error handling widget comm message', e);
                }
            };
        }
        catch (e) {
            dbg('Failed to attach onMsg to widget comm', e);
        }
    };
    try {
        kernelConn.registerCommTarget('jupyter.widget', simpleHandler);
        kernelConn.registerCommTarget('jupyter.widget.control', simpleHandler);
    }
    catch (e) {
        dbg('Widget comm target registration failed', e);
    }
    return () => {
        try {
            if (typeof kernelConn.unregisterCommTarget === 'function') {
                try {
                    kernelConn.unregisterCommTarget('jupyter.widget');
                }
                catch (e) {
                    /* ignore */
                }
                try {
                    kernelConn.unregisterCommTarget('jupyter.widget.control');
                }
                catch (e) {
                    /* ignore */
                }
            }
        }
        catch (e) {
            dbg('Error during widget comm cleanup', e);
        }
    };
}
// -- Global registration helper ------------------------------------------------



/**
 * Toggle whether the frontend should attach to `KernelAPI.runningChanged`
 * (or use polling) to detect new/removed kernels. Set to `false` to
 * disable dynamic detection; initial registration still runs.
 */
const ENABLE_RUNNING_CHANGED = false;
/**
 * Register a global comm target `jupyter.ggblab` on all currently
 * running kernels by creating lightweight KernelConnection instances
 * and registering a simple handler. Returns an unregister function.
 *
 * Note: This is a pragmatic approach (B). It creates front-end KernelConnection
 * objects for each running kernel so the front-end can listen for comm opens
 * from kernels that target `jupyter.ggblab`.
 */
async function registerGlobalGGBlabCommTargets(app) {
    const baseUrl = _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_1__.PageConfig.getBaseUrl();
    const token = _jupyterlab_coreutils__WEBPACK_IMPORTED_MODULE_1__.PageConfig.getToken();
    const settings = _jupyterlab_services__WEBPACK_IMPORTED_MODULE_0__.ServerConnection.makeSettings({
        baseUrl: baseUrl,
        token: token,
        appendToken: true
    });
    // Map kernelId -> unregister function
    const registry = new Map();
    const dbg = (..._args) => {
        // Only emit debug logs when dynamic detection is enabled to avoid
        // noisy 'Already registered' messages during normal startup.
        if (!ENABLE_RUNNING_CHANGED) {
            return;
        }
        try {
            console.debug(..._args);
        }
        catch (e) {
            /* ignore */
        }
    };
    const registerKernel = (k) => {
        const id = k.id || k.kernelId || (k.model && k.model.id) || null;
        if (!id) {
            return;
        }
        if (registry.has(id)) {
            dbg('Already registered jupyter.ggblab for kernel', id);
            return;
        }
        try {
            // If a widget manager is available and implements a GGBlab comm
            // registration API, delegate the handler registration to it so that
            // message routing can be handled by the manager (DOM lifecycle etc.).
            const manager = createWidgetManager();
            if (manager && typeof manager.registerGGBlabHandler === 'function') {
                try {
                    const unregisterFromManager = manager.registerGGBlabHandler(id, (commOp, msg) => {
                        try {
                            // Delegate to manager for message routing.
                            // Manager may handle commOp and msg directly.
                            // If it does not, manager implementors should call commOp.onMsg themselves.
                        }
                        catch (e) {
                            console.warn('Error delegating jupyter.ggblab to manager', e);
                        }
                    });
                    registry.set(id, () => {
                        try {
                            unregisterFromManager && unregisterFromManager();
                        }
                        catch (e) {
                            /* ignore */
                        }
                    });
                    return;
                }
                catch (e) {
                    console.warn('Widget manager failed to register jupyter.ggblab', id, e);
                }
            }
            // Fallback: register a lightweight KernelConnection-based handler
            const kc = new _jupyterlab_services__WEBPACK_IMPORTED_MODULE_0__.KernelConnection({
                model: { name: 'python3', id },
                serverSettings: settings
            });
            try {
                kc.registerCommTarget('jupyter.ggblab', (commOp, msg) => {
                    try {
                        dbg('jupyter.ggblab comm opened', { kernelId: id, msg });
                        try {
                            commOp.onMsg = (m) => {
                                dbg('jupyter.ggblab message', { kernelId: id, m });
                            };
                        }
                        catch (e) {
                            /* ignore */
                        }
                    }
                    catch (e) {
                        console.warn('Error in jupyter.ggblab handler', e);
                    }
                });
            }
            catch (e) {
                console.warn('Failed to register jupyter.ggblab on kernel', id, e);
            }
            const unregister = () => {
                try {
                    if (typeof kc.unregisterCommTarget === 'function') {
                        try {
                            kc.unregisterCommTarget('jupyter.ggblab');
                        }
                        catch (e) {
                            /* ignore */
                        }
                    }
                }
                catch (e) {
                    console.warn('Error while unregistering jupyter.ggblab', e);
                }
            };
            registry.set(id, unregister);
        }
        catch (e) {
            console.warn('Failed to create KernelConnection for kernel', id, e);
        }
    };
    const unregisterKernel = (id) => {
        const fn = registry.get(id);
        if (fn) {
            try {
                fn();
            }
            catch (e) {
                console.warn('Error during unregister for kernel', id, e);
            }
            registry.delete(id);
        }
    };
    // Initial registration for running kernels
    try {
        const kernels = await _jupyterlab_services__WEBPACK_IMPORTED_MODULE_0__.KernelAPI.listRunning();
        (kernels || []).forEach(registerKernel);
    }
    catch (e) {
        console.warn('Failed to list running kernels for ggblab registration', e);
    }
    // Watch for changes in running kernels and keep registry in sync.
    const onRunningChanged = async () => {
        try {
            const current = await _jupyterlab_services__WEBPACK_IMPORTED_MODULE_0__.KernelAPI.listRunning();
            const currentIds = new Set((current || []).map((k) => k.id));
            // register new
            (current || []).forEach(k => registerKernel(k));
            // unregister removed
            Array.from(registry.keys()).forEach(id => {
                if (!currentIds.has(id)) {
                    unregisterKernel(id);
                }
            });
        }
        catch (e) {
            console.warn('Error handling runningChanged for ggblab', e);
        }
    };
    try {
        // Optionally attach to runningChanged or poll; respect global flag.
        if (ENABLE_RUNNING_CHANGED) {
            // Prefer JupyterLab's session manager signal when `app` is provided.
            try {
                if (app &&
                    app.serviceManager &&
                    app.serviceManager.sessions &&
                    typeof app.serviceManager.sessions.runningChanged === 'object' &&
                    typeof app.serviceManager.sessions.runningChanged.connect ===
                        'function') {
                    app.serviceManager.sessions.runningChanged.connect(onRunningChanged);
                }
                else if (_jupyterlab_services__WEBPACK_IMPORTED_MODULE_0__.KernelAPI.runningChanged &&
                    typeof _jupyterlab_services__WEBPACK_IMPORTED_MODULE_0__.KernelAPI.runningChanged.connect === 'function') {
                    _jupyterlab_services__WEBPACK_IMPORTED_MODULE_0__.KernelAPI.runningChanged.connect(onRunningChanged);
                }
                else {
                    // Fallback: poll periodically (conservative) — safe but less efficient.
                    const pollInterval = 5000;
                    const timer = setInterval(onRunningChanged, pollInterval);
                    // store a dummy unregister that clears timer
                    registry.set('__poll_timer__', () => clearInterval(timer));
                }
            }
            catch (e) {
                console.warn('Failed to attach runningChanged listener', e);
            }
        }
        else {
            // Dynamic detection disabled by flag; do nothing here.
            dbg('Kernel runningChanged detection is disabled (ENABLE_RUNNING_CHANGED=false)');
        }
    }
    catch (e) {
        console.warn('Failed to attach runningChanged listener', e);
    }
    // Return an unregister-all function
    return () => {
        try {
            try {
                if (app &&
                    app.serviceManager &&
                    app.serviceManager.sessions &&
                    typeof app.serviceManager.sessions.runningChanged === 'object' &&
                    typeof app.serviceManager.sessions.runningChanged.disconnect ===
                        'function') {
                    try {
                        app.serviceManager.sessions.runningChanged.disconnect(onRunningChanged);
                    }
                    catch (e) {
                        /* ignore */
                    }
                }
                else if (_jupyterlab_services__WEBPACK_IMPORTED_MODULE_0__.KernelAPI.runningChanged &&
                    typeof _jupyterlab_services__WEBPACK_IMPORTED_MODULE_0__.KernelAPI.runningChanged.disconnect === 'function') {
                    try {
                        _jupyterlab_services__WEBPACK_IMPORTED_MODULE_0__.KernelAPI.runningChanged.disconnect(onRunningChanged);
                    }
                    catch (e) {
                        /* ignore */
                    }
                }
            }
            catch (e) {
                /* ignore */
            }
            // Call all unregister functions
            Array.from(registry.keys()).forEach(k => {
                try {
                    const fn = registry.get(k);
                    if (fn) {
                        fn();
                    }
                }
                catch (e) {
                    /* ignore */
                }
            });
            registry.clear();
        }
        catch (e) {
            console.warn('Error during global ggblab unregister-all', e);
        }
    };
}


/***/ },

/***/ "./package.json"
/*!**********************!*\
  !*** ./package.json ***!
  \**********************/
(module) {

module.exports = /*#__PURE__*/JSON.parse('{"name":"ggblab","version":"1.2.4","description":"A JupyterLab extension for learning geometry and Python programming side-by-side with GeoGebra.","keywords":["jupyter","jupyterlab","jupyterlab-extension"],"homepage":"https://github.com/moyhig-ecs/ggblab#readme","bugs":{"url":"https://github.com/moyhig-ecs/ggblab/issues"},"license":"BSD-3-Clause","author":{"name":"Manabu Higashida","email":"manabu@higashida.net"},"files":["lib/**/*.{d.ts,eot,gif,html,jpg,js,js.map,json,png,svg,woff2,ttf}","style/**/*.{css,js,eot,gif,html,jpg,json,png,svg,woff2,ttf}","src/**/*.{ts,tsx}","schema/*.json"],"main":"lib/index.js","types":"lib/index.d.ts","style":"style/index.css","repository":{"type":"git","url":"https://github.com/moyhig-ecs/ggblab"},"scripts":{"build":"jlpm build:lib && jlpm build:labextension:dev","build:prod":"jlpm clean && jlpm build:lib:prod && jlpm build:labextension","build:labextension":"jupyter labextension build .","build:labextension:dev":"jupyter labextension build --development True .","build:lib":"tsc --sourceMap","build:lib:prod":"tsc","clean":"jlpm clean:lib","clean:lib":"rimraf lib tsconfig.tsbuildinfo","clean:lintcache":"rimraf .eslintcache .stylelintcache","clean:labextension":"rimraf ggblab/labextension ggblab/_version.py","clean:all":"jlpm clean:lib && jlpm clean:labextension && jlpm clean:lintcache","eslint":"jlpm eslint:check --fix","eslint:check":"eslint . --cache --ext .ts,.tsx","install:extension":"jlpm build","lint":"jlpm stylelint && jlpm prettier && jlpm eslint","lint:check":"jlpm stylelint:check && jlpm prettier:check && jlpm eslint:check","prettier":"jlpm prettier:base --write --list-different","prettier:base":"prettier \\"**/*{.ts,.tsx,.js,.jsx,.css,.json,.md}\\"","prettier:check":"jlpm prettier:base --check","stylelint":"jlpm stylelint:check --fix","stylelint:check":"stylelint --cache \\"style/**/*.css\\"","test":"jest --coverage","watch":"run-p watch:src watch:labextension","watch:src":"tsc -w --sourceMap","watch:labextension":"jupyter labextension watch ."},"dependencies":{"@jupyter-widgets/base":"^4.0.0","@jupyterlab/application":"^4.0.0","@jupyterlab/apputils":"^4.6.1","@jupyterlab/launcher":"^4.5.1","@jupyterlab/settingregistry":"^4.0.0","@lumino/widgets":"^2.7.2","@marshallku/react-postscribe":"^0.2.0","react-meta-tags":"^1.0.1"},"devDependencies":{"@jupyterlab/builder":"^4.5.2","@jupyterlab/testutils":"^4.0.0","@types/jest":"^29.2.0","@types/json-schema":"^7.0.11","@types/react":"^18.0.26","@types/react-addons-linked-state-mixin":"^0.14.22","@typescript-eslint/eslint-plugin":"^6.1.0","@typescript-eslint/parser":"^6.1.0","css-loader":"^6.7.1","eslint":"^8.36.0","eslint-config-prettier":"^8.8.0","eslint-plugin-prettier":"^5.0.0","jest":"^29.2.0","npm-run-all2":"^7.0.1","prettier":"^3.0.0","rimraf":"^5.0.1","source-map-loader":"^1.0.2","style-loader":"^3.3.1","stylelint":"^15.10.1","stylelint-config-recommended":"^13.0.0","stylelint-config-standard":"^34.0.0","stylelint-csstree-validator":"^3.0.0","stylelint-prettier":"^4.0.0","typescript":"~5.5.4","yjs":"^13.5.0"},"resolutions":{"lib0":"0.2.111"},"sideEffects":["style/*.css","style/index.js"],"styleModule":"style/index.js","publishConfig":{"access":"public"},"jupyterlab":{"extension":true,"outputDir":"ggblab/labextension","schemaDir":"schema"},"eslintIgnore":["node_modules","dist","coverage","**/*.d.ts","tests","**/__tests__","ui-tests"],"eslintConfig":{"extends":["eslint:recommended","plugin:@typescript-eslint/eslint-recommended","plugin:@typescript-eslint/recommended","plugin:prettier/recommended"],"parser":"@typescript-eslint/parser","parserOptions":{"project":"tsconfig.json","sourceType":"module"},"plugins":["@typescript-eslint"],"rules":{"@typescript-eslint/naming-convention":["error",{"selector":"interface","format":["PascalCase"],"custom":{"regex":"^I[A-Z]","match":true}}],"@typescript-eslint/no-unused-vars":["warn",{"args":"none"}],"@typescript-eslint/no-explicit-any":"off","@typescript-eslint/no-namespace":"off","@typescript-eslint/no-use-before-define":"off","@typescript-eslint/quotes":["error","single",{"avoidEscape":true,"allowTemplateLiterals":false}],"curly":["error","all"],"eqeqeq":"error","prefer-arrow-callback":"error"}},"prettier":{"singleQuote":true,"trailingComma":"none","arrowParens":"avoid","endOfLine":"auto","overrides":[{"files":"package.json","options":{"tabWidth":4}}]},"stylelint":{"extends":["stylelint-config-recommended","stylelint-config-standard","stylelint-prettier/recommended"],"plugins":["stylelint-csstree-validator"],"rules":{"csstree/validator":true,"property-no-vendor-prefix":null,"selector-class-pattern":"^([a-z][A-z\\\\d]*)(-[A-z\\\\d]+)*$","selector-no-vendor-prefix":null,"value-no-vendor-prefix":null}}}');

/***/ }

}]);
//# sourceMappingURL=lib_index_js.c05dd9c04c50f47c33a2.js.map