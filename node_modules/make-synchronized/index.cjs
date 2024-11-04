var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// source/index.js
var source_exports = {};
__export(source_exports, {
  default: () => source_default,
  makeDefaultExportSynchronized: () => makeDefaultExportSynchronized,
  makeModuleSynchronized: () => makeModuleSynchronized,
  makeSynchronized: () => makeSynchronized,
  makeSynchronizedFunction: () => makeSynchronizedFunction,
  makeSynchronizedFunctions: () => makeSynchronizedFunctions
});
module.exports = __toCommonJS(source_exports);
var import_node_worker_threads3 = require("node:worker_threads");

// source/constants.js
var path = __toESM(require("node:path"), 1);
var WORKER_FILE_NAME = "worker.mjs";
var {
  // @ts-expect-error -- ?
  WORKER_ACTION_APPLY,
  // @ts-expect-error -- ?
  WORKER_ACTION_GET,
  // @ts-expect-error -- ?
  WORKER_ACTION_OWN_KEYS,
  // @ts-expect-error -- ?
  WORKER_ACTION_GET_INFORMATION,
  // @ts-expect-error -- ?
  VALUE_TYPE_FUNCTION,
  // @ts-expect-error -- ?
  VALUE_TYPE_PRIMITIVE,
  // @ts-expect-error -- ?
  VALUE_TYPE_PLAIN_OBJECT,
  // @ts-expect-error -- ?
  VALUE_TYPE_UNKNOWN
} = new Proxy(
  {},
  {
    get: (
      /** @param {string} property */
      (_, property) => `[[${property}]]`
    )
  }
);
var WORKER_FILE = path.join(__dirname, WORKER_FILE_NAME);
var IS_PRODUCTION = true;

// source/to-module-id.js
var url = __toESM(require("node:url"), 1);
var path2 = __toESM(require("node:path"), 1);
function toModuleId(module2) {
  if (module2 instanceof URL) {
    return module2.href;
  }
  if (typeof module2 === "string" && path2.isAbsolute(module2)) {
    return url.pathToFileURL(module2).href;
  }
  if (typeof module2?.url === "string" && module2.url.startsWith("file://")) {
    return module2.url;
  }
  return module2;
}
var to_module_id_default = toModuleId;

// source/property-path.js
var normalizePath = (propertyOrPath = []) => Array.isArray(propertyOrPath) ? propertyOrPath : [propertyOrPath];
var hashPath = (path3) => JSON.stringify(normalizePath(path3));

// source/threads-worker.js
var import_node_worker_threads2 = require("node:worker_threads");
var import_node_process = __toESM(require("node:process"), 1);

// source/atomics-wait-error.js
var AtomicsWaitError = class extends Error {
  code = "";
  name = "AtomicsWaitError";
  constructor(code) {
    super(code === "timed-out" ? "Timed out" : "Unexpected error");
    this.code = code;
  }
};
var atomics_wait_error_default = AtomicsWaitError;

// source/lock.js
var UNLOCKED = 2;
var Lock = class _Lock {
  /** @param {Int32Array} semaphore */
  static signal(semaphore) {
    return new _Lock(semaphore).unlock();
  }
  semaphore;
  constructor(semaphore = new Int32Array(new SharedArrayBuffer(4))) {
    this.semaphore = semaphore;
  }
  /** @param {number} [timeout] */
  lock(timeout) {
    const { semaphore } = this;
    this.semaphore = void 0;
    if (semaphore[0] === UNLOCKED) {
      return;
    }
    const status = Atomics.wait(semaphore, 0, 0, timeout);
    if (status === "ok") {
      return;
    }
    throw new atomics_wait_error_default(status);
  }
  unlock() {
    const { semaphore } = this;
    Atomics.store(semaphore, 0, UNLOCKED);
    Atomics.notify(semaphore, 0);
  }
};
var lock_default = Lock;

// source/request.js
var import_node_worker_threads = require("node:worker_threads");
var util = __toESM(require("node:util"), 1);
function request(worker, action, payload, timeout) {
  const lock = new lock_default();
  const { port1: mainThreadPort, port2: workerPort } = new import_node_worker_threads.MessageChannel();
  try {
    worker.postMessage(
      {
        responseSemaphore: lock.semaphore,
        responsePort: workerPort,
        action,
        payload
      },
      [workerPort]
    );
  } catch {
    throw Object.assign(
      new Error(`Cannot serialize request data:
${util.inspect(payload)}`),
      { requestData: payload }
    );
  }
  lock.lock(timeout);
  const { message } = (0, import_node_worker_threads.receiveMessageOnPort)(mainThreadPort);
  return message;
}
var request_default = request;

// source/threads-worker.js
var ThreadsWorker = class {
  /** @type {Worker} */
  #worker;
  #workerData;
  constructor(workerData) {
    this.#workerData = workerData;
  }
  sendAction(action, payload) {
    this.#worker ??= this.#createWorker();
    return this.#sendActionToWorker(this.#worker, action, payload);
  }
  /**
  @returns {Worker}
  */
  #createWorker() {
    const lock = IS_PRODUCTION ? {} : new lock_default();
    const worker = new import_node_worker_threads2.Worker(WORKER_FILE, {
      workerData: {
        workerRunningSemaphore: lock.semaphore,
        ...this.#workerData
      },
      // https://nodejs.org/api/worker_threads.html#new-workerfilename-options
      // Do not pipe `stdio`s
      stdout: true,
      stderr: true
    });
    worker.unref();
    if (IS_PRODUCTION) {
      return worker;
    }
    try {
      lock.lock(1e3);
    } catch (error) {
      if (error instanceof atomics_wait_error_default) {
        throw new Error(
          `Unexpected error, most likely caused by syntax error in '${WORKER_FILE}'`
        );
      }
      throw error;
    }
    return worker;
  }
  /**
  @param {Worker} worker
  @param {string} action
  @param {Record<string, any>} payload
  @param {number} [timeout]
  */
  #sendActionToWorker(worker, action, payload, timeout) {
    const { stdio, result, error, errorData, terminated } = request_default(
      worker,
      action,
      payload,
      timeout
    );
    for (const { stream, chunk } of stdio) {
      import_node_process.default[stream].write(chunk);
    }
    if (terminated && this.#worker) {
      this.#worker.terminate();
      this.#worker = void 0;
    }
    if (error) {
      throw Object.assign(error, errorData);
    }
    return result;
  }
};
var threads_worker_default = ThreadsWorker;

// source/synchronizer.js
var cacheResult = (cache, cacheKey, getResult) => {
  if (!cache.has(cacheKey)) {
    cache.set(cacheKey, getResult());
  }
  return cache.get(cacheKey);
};
var cachePathResult = (cache, path3, getResult) => cacheResult(cache, hashPath(path3), getResult);
var Synchronizer = class _Synchronizer {
  static #instances = /* @__PURE__ */ new Map();
  /**
   @param {{module: Module}} param0
   @returns {Synchronizer}
   */
  static create({ module: module2 }) {
    const moduleId = to_module_id_default(module2);
    return cacheResult(
      this.#instances,
      moduleId,
      () => new _Synchronizer(moduleId)
    );
  }
  #worker;
  #synchronizedFunctionStore = /* @__PURE__ */ new Map();
  #informationStore = /* @__PURE__ */ new Map();
  #ownKeysStore = /* @__PURE__ */ new Map();
  #plainObjectStore = /* @__PURE__ */ new Map();
  constructor(moduleId) {
    this.#worker = new threads_worker_default({ moduleId });
  }
  getInformation(path3) {
    return cachePathResult(
      this.#informationStore,
      path3,
      () => this.#worker.sendAction(WORKER_ACTION_GET_INFORMATION, { path: path3 })
    );
  }
  get(path3) {
    const information = this.getInformation(path3);
    switch (information.type) {
      case VALUE_TYPE_FUNCTION:
        return this.#createSynchronizedFunction(path3);
      case VALUE_TYPE_PRIMITIVE:
        return information.value;
      case VALUE_TYPE_PLAIN_OBJECT:
        return this.#createPlainObjectProxy(path3, information);
      default:
        return this.#worker.sendAction(WORKER_ACTION_GET, { path: path3 });
    }
  }
  ownKeys(path3) {
    return cachePathResult(
      this.#ownKeysStore,
      path3,
      () => this.#worker.sendAction(WORKER_ACTION_OWN_KEYS, { path: path3 })
    );
  }
  apply(path3, argumentsList) {
    return this.#worker.sendAction(WORKER_ACTION_APPLY, { path: path3, argumentsList });
  }
  #createSynchronizedFunction(path3) {
    return cachePathResult(
      this.#synchronizedFunctionStore,
      path3,
      () => (...argumentsList) => this.apply(path3, argumentsList)
    );
  }
  /** @return {SynchronizedDefaultExportProxy} */
  createDefaultExportFunctionProxy() {
    const defaultExportFunction = this.get("default");
    return new Proxy(defaultExportFunction, {
      get: (target, property) => this.get(property)
    });
  }
  #createPlainObjectProxy(path3, { isNullPrototypeObject, properties }) {
    path3 = normalizePath(path3);
    return cachePathResult(this.#plainObjectStore, path3, () => {
      const object = isNullPrototypeObject ? /* @__PURE__ */ Object.create(null) : {};
      for (const [property, propertyInformation] of properties) {
        if (propertyInformation?.type === VALUE_TYPE_PRIMITIVE) {
          object[property] = propertyInformation.value;
        } else {
          Object.defineProperty(object, property, {
            get: () => this.get([...path3, property]),
            enumerable: true,
            configurable: true
          });
        }
      }
      return new Proxy(object, {
        get: (target, property, receiver) => {
          if (typeof property === "symbol" || properties.has(property)) {
            return Reflect.get(target, property, receiver);
          }
          return this.get([...path3, property]);
        }
      });
    });
  }
  /** @return {SynchronizedModule} */
  createModule() {
    const module2 = Object.create(null, {
      [Symbol.toStringTag]: { value: "Module", enumerable: false }
    });
    const specifiers = this.ownKeys();
    return Object.defineProperties(
      module2,
      Object.fromEntries(
        specifiers.map((specifier) => [
          specifier,
          {
            get: () => this.get(specifier),
            enumerable: true
          }
        ])
      )
    );
  }
};
var synchronizer_default = Synchronizer;

// source/index.js
function makeSynchronizedFunctions(module2, implementation) {
  if (!import_node_worker_threads3.isMainThread) {
    return implementation;
  }
  const synchronizer = synchronizer_default.create({ module: module2 });
  return new Proxy(implementation, {
    get: (target, property) => (
      // @ts-expect-error -- ?
      typeof implementation[property] === "function" ? synchronizer.get(property) : (
        // @ts-expect-error -- ?
        target[property]
      )
    )
  });
}
function makeSynchronizedFunction(module2, implementation, specifier = "default") {
  if (!import_node_worker_threads3.isMainThread) {
    return implementation;
  }
  const synchronizer = synchronizer_default.create({ module: module2 });
  return synchronizer.get(specifier);
}
function makeDefaultExportSynchronized(module2) {
  return synchronizer_default.create({ module: module2 }).get("default");
}
function makeModuleSynchronized(module2) {
  return synchronizer_default.create({ module: module2 }).createModule();
}
function makeSynchronized(module2, implementation) {
  if (typeof implementation === "function") {
    return makeSynchronizedFunction(module2, implementation);
  }
  if (implementation) {
    return makeSynchronizedFunctions(module2, implementation);
  }
  const synchronizer = synchronizer_default.create({ module: module2 });
  const defaultExportType = synchronizer.getInformation("default").type;
  if (defaultExportType === VALUE_TYPE_FUNCTION) {
    return synchronizer.createDefaultExportFunctionProxy();
  }
  return synchronizer.createModule();
}
var source_default = makeSynchronized;
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  makeDefaultExportSynchronized,
  makeModuleSynchronized,
  makeSynchronized,
  makeSynchronizedFunction,
  makeSynchronizedFunctions
});
