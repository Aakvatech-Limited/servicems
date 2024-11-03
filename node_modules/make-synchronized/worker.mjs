// source/worker.js
import { parentPort, workerData } from "node:worker_threads";

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
var STDIO_STREAMS = ["stdout", "stderr"];

// source/get-value-information.js
function getPlainObjectPropertyInformation(object, key) {
  const descriptor = Object.getOwnPropertyDescriptor(object, key);
  if (!Object.hasOwn(descriptor, "value")) {
    return;
  }
  const { value } = descriptor;
  const type = typeof value;
  if (value === null || type === "undefined" || type === "boolean" || type === "number" || type === "bigint" || type === "string") {
    return { type: VALUE_TYPE_PRIMITIVE, value };
  }
}
function getValueInformation(value) {
  if (typeof value === "function") {
    return { type: VALUE_TYPE_FUNCTION };
  }
  const type = typeof value;
  if (value === null || type === "undefined" || type === "boolean" || type === "number" || type === "bigint" || type === "string") {
    return { type: VALUE_TYPE_PRIMITIVE, value };
  }
  const information = { type: VALUE_TYPE_UNKNOWN };
  if (Object.getPrototypeOf(value) === null) {
    information.type = VALUE_TYPE_PLAIN_OBJECT;
    information.isNullPrototypeObject = true;
  }
  if (value.constructor === Object) {
    information.type = VALUE_TYPE_PLAIN_OBJECT;
  }
  if (information.type === VALUE_TYPE_PLAIN_OBJECT) {
    information.properties = new Map(
      Object.keys(value).map((property) => [
        property,
        getPlainObjectPropertyInformation(value, property)
      ])
    );
  }
  return information;
}
var get_value_information_default = getValueInformation;

// source/property-path.js
var normalizePath = (propertyOrPath = []) => Array.isArray(propertyOrPath) ? propertyOrPath : [propertyOrPath];

// source/response.js
import process from "node:process";
import util from "node:util";

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

// source/response.js
var processExit = process.exit;
var Response = class {
  #responseSemaphore;
  #responsePort;
  #actionHandlers;
  #stdio = [];
  constructor(actionHandlers2) {
    this.#actionHandlers = actionHandlers2;
    process.exit = () => {
      this.#terminate();
      processExit();
    };
    for (const stream of STDIO_STREAMS) {
      process[stream]._writev = (chunks, callback) => {
        for (const { chunk } of chunks) {
          this.#stdio.push({ stream, chunk });
        }
        callback();
      };
    }
  }
  #send(response2) {
    const responsePort = this.#responsePort;
    try {
      responsePort.postMessage({ ...response2, stdio: this.#stdio });
    } catch {
      const error = new Error(
        `Cannot serialize worker response:
${util.inspect(response2.result)}`
      );
      responsePort.postMessage({ error, stdio: this.#stdio });
    } finally {
      this.#finish();
    }
  }
  #sendResult(result) {
    this.#send({ result });
  }
  #throws(error) {
    this.#send({ error, errorData: { ...error } });
  }
  #finish() {
    lock_default.signal(this.#responseSemaphore);
    process.exitCode = void 0;
    this.#responsePort.close();
    this.#stdio.length = 0;
  }
  #terminate() {
    this.#send({ terminated: true });
  }
  #processAction(action, payload) {
    const handler = this.#actionHandlers[action];
    if (!handler) {
      throw new Error(`Unknown action '${action}'.`);
    }
    return handler(payload);
  }
  listen(receivePort) {
    receivePort.addListener(
      "message",
      async ({ responseSemaphore, responsePort, action, payload }) => {
        this.#responseSemaphore = responseSemaphore;
        this.#responsePort = responsePort;
        try {
          this.#sendResult(await this.#processAction(action, payload));
        } catch (error) {
          this.#throws(error);
        }
      }
    );
  }
};
var response_default = Response;

// source/worker.js
var { workerRunningSemaphore, moduleId } = workerData;
async function getValue(payload) {
  let value = await import(moduleId);
  let receiver;
  for (const property of normalizePath(payload.path)) {
    receiver = value;
    value = Reflect.get(value, property, value);
  }
  return { value, receiver };
}
var actionHandlers = {
  async [WORKER_ACTION_GET](payload) {
    const { value } = await getValue(payload);
    return value;
  },
  async [WORKER_ACTION_APPLY](payload) {
    const { value: method, receiver } = await getValue(payload);
    return Reflect.apply(method, receiver, payload.argumentsList);
  },
  async [WORKER_ACTION_OWN_KEYS](payload) {
    const { value } = await getValue(payload);
    return Reflect.ownKeys(value).filter((key) => typeof key !== "symbol");
  },
  async [WORKER_ACTION_GET_INFORMATION](payload) {
    const { value } = await getValue(payload);
    return get_value_information_default(value);
  }
};
if (workerRunningSemaphore) {
  lock_default.signal(workerRunningSemaphore);
}
var response = new response_default(actionHandlers);
response.listen(parentPort);
