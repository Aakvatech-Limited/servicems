// source/index.js
import { isMainThread } from "node:worker_threads";

// source/constants.js
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
var WORKER_FILE = new URL(WORKER_FILE_NAME, import.meta.url);
var IS_PRODUCTION = true;

// source/to-module-id.js
import * as url from "node:url";
import * as path from "node:path";
function toModuleId(module) {
  if (module instanceof URL) {
    return module.href;
  }
  if (typeof module === "string" && path.isAbsolute(module)) {
    return url.pathToFileURL(module).href;
  }
  if (typeof module?.url === "string" && module.url.startsWith("file://")) {
    return module.url;
  }
  return module;
}
var to_module_id_default = toModuleId;

// source/property-path.js
var normalizePath = (propertyOrPath = []) => Array.isArray(propertyOrPath) ? propertyOrPath : [propertyOrPath];
var hashPath = (path2) => JSON.stringify(normalizePath(path2));

// source/threads-worker.js
import { Worker } from "node:worker_threads";
import process from "node:process";

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
import { receiveMessageOnPort, MessageChannel } from "node:worker_threads";
import * as util from "node:util";
function request(worker, action, payload, timeout) {
  const lock = new lock_default();
  const { port1: mainThreadPort, port2: workerPort } = new MessageChannel();
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
  const { message } = receiveMessageOnPort(mainThreadPort);
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
    const worker = new Worker(WORKER_FILE, {
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
      process[stream].write(chunk);
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
var cachePathResult = (cache, path2, getResult) => cacheResult(cache, hashPath(path2), getResult);
var Synchronizer = class _Synchronizer {
  static #instances = /* @__PURE__ */ new Map();
  /**
   @param {{module: Module}} param0
   @returns {Synchronizer}
   */
  static create({ module }) {
    const moduleId = to_module_id_default(module);
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
  getInformation(path2) {
    return cachePathResult(
      this.#informationStore,
      path2,
      () => this.#worker.sendAction(WORKER_ACTION_GET_INFORMATION, { path: path2 })
    );
  }
  get(path2) {
    const information = this.getInformation(path2);
    switch (information.type) {
      case VALUE_TYPE_FUNCTION:
        return this.#createSynchronizedFunction(path2);
      case VALUE_TYPE_PRIMITIVE:
        return information.value;
      case VALUE_TYPE_PLAIN_OBJECT:
        return this.#createPlainObjectProxy(path2, information);
      default:
        return this.#worker.sendAction(WORKER_ACTION_GET, { path: path2 });
    }
  }
  ownKeys(path2) {
    return cachePathResult(
      this.#ownKeysStore,
      path2,
      () => this.#worker.sendAction(WORKER_ACTION_OWN_KEYS, { path: path2 })
    );
  }
  apply(path2, argumentsList) {
    return this.#worker.sendAction(WORKER_ACTION_APPLY, { path: path2, argumentsList });
  }
  #createSynchronizedFunction(path2) {
    return cachePathResult(
      this.#synchronizedFunctionStore,
      path2,
      () => (...argumentsList) => this.apply(path2, argumentsList)
    );
  }
  /** @return {SynchronizedDefaultExportProxy} */
  createDefaultExportFunctionProxy() {
    const defaultExportFunction = this.get("default");
    return new Proxy(defaultExportFunction, {
      get: (target, property) => this.get(property)
    });
  }
  #createPlainObjectProxy(path2, { isNullPrototypeObject, properties }) {
    path2 = normalizePath(path2);
    return cachePathResult(this.#plainObjectStore, path2, () => {
      const object = isNullPrototypeObject ? /* @__PURE__ */ Object.create(null) : {};
      for (const [property, propertyInformation] of properties) {
        if (propertyInformation?.type === VALUE_TYPE_PRIMITIVE) {
          object[property] = propertyInformation.value;
        } else {
          Object.defineProperty(object, property, {
            get: () => this.get([...path2, property]),
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
          return this.get([...path2, property]);
        }
      });
    });
  }
  /** @return {SynchronizedModule} */
  createModule() {
    const module = Object.create(null, {
      [Symbol.toStringTag]: { value: "Module", enumerable: false }
    });
    const specifiers = this.ownKeys();
    return Object.defineProperties(
      module,
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
function makeSynchronizedFunctions(module, implementation) {
  if (!isMainThread) {
    return implementation;
  }
  const synchronizer = synchronizer_default.create({ module });
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
function makeSynchronizedFunction(module, implementation, specifier = "default") {
  if (!isMainThread) {
    return implementation;
  }
  const synchronizer = synchronizer_default.create({ module });
  return synchronizer.get(specifier);
}
function makeDefaultExportSynchronized(module) {
  return synchronizer_default.create({ module }).get("default");
}
function makeModuleSynchronized(module) {
  return synchronizer_default.create({ module }).createModule();
}
function makeSynchronized(module, implementation) {
  if (typeof implementation === "function") {
    return makeSynchronizedFunction(module, implementation);
  }
  if (implementation) {
    return makeSynchronizedFunctions(module, implementation);
  }
  const synchronizer = synchronizer_default.create({ module });
  const defaultExportType = synchronizer.getInformation("default").type;
  if (defaultExportType === VALUE_TYPE_FUNCTION) {
    return synchronizer.createDefaultExportFunctionProxy();
  }
  return synchronizer.createModule();
}
var source_default = makeSynchronized;
export {
  source_default as default,
  makeDefaultExportSynchronized,
  makeModuleSynchronized,
  makeSynchronized,
  makeSynchronizedFunction,
  makeSynchronizedFunctions
};
