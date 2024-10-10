import fs from 'fs';
import path from 'path';
import { format } from 'date-fns';

class CustomLogger {
  constructor(config) {
    // console.log('CustomLogger constructor called with config:', JSON.stringify(config));
    if (!config) {
      throw new Error('Config is undefined');
    }
    this.config = config;
    this.logStream = null;
    this.currentLogFile = null;
    this.logStartTime = Date.now();;
    this.isRotating = false;
    
    this.setupNewLogFile();
  }

  setupNewLogFile() {
    // console.log('setupNewLogFile called');
    this.isRotating = true;
    const timestamp = format(new Date(), 'yyyy-MM-dd_HH-mm-ss');
    if (!this.config.directory) {
      throw new Error('Logging directory is not defined in the config');
    }
    this.currentLogFile = path.join(this.config.directory, `backend_${timestamp}.log`);
    fs.mkdirSync(this.config.directory, { recursive: true });
    if (this.logStream) this.logStream.end();
    this.logStream = fs.createWriteStream(this.currentLogFile, { flags: 'a' });
    this.logStartTime = Date.now();
    this.isRotating = false;
    console.log('New log file setup:', this.currentLogFile);
  }

  getFormattedLog(args) {
    const timestamp = format(new Date(), 'yyyy-MM-dd HH:mm:ss');
    return `${timestamp} ${args.map(arg => (typeof arg === 'string' ? arg : JSON.stringify(arg))).join(' ')}`;
  }

  log(...args) {
    this._writeLog('log', ...args);
  }

  error(...args) {
    this._writeLog('error', ...args);
  }

  _writeLog(method, ...args) {
    if (!this.isRotating) {
      if (this.config.toConsole) console[method](...args);
      if (this.config.toFile && this.logStream) {
        this.logStream.write(this.getFormattedLog(args));
        this.logStream.write('\n');
      }
    }
  }

  	
  close() {
    if (this.logStream) {
      this.logStream.end();
      this.logStream = null;
    }
  }
}

let loggerInstance = null;

export function setupLogger(config) {
  if (loggerInstance) {
    console.warn('Existing logger instance found. Use resetLogger() to create a new instance.');
    return { logger: loggerInstance, logStartTime: loggerInstance.logStartTime };
  }
  if (!config || typeof config !== 'object') {
    throw new Error('Invalid config: config must be an object');
  }
  loggerInstance = new CustomLogger(config);
  return { logger: loggerInstance, logStartTime: loggerInstance.logStartTime };
}

export function getLogger() {
  if (!loggerInstance) {
    throw new Error('Logger not initialized. Call setupLogger first.');
  }
  return { logger: loggerInstance, logStartTime: loggerInstance.logStartTime };
}

export function resetLogger(config) {
  if (loggerInstance) {
    loggerInstance.close();
    loggerInstance = null;
  }
  if (!config || typeof config !== 'object') {
    throw new Error('Invalid config: config must be an object');
  }
  loggerInstance = new CustomLogger(config);
  return { logger: loggerInstance, logStartTime: loggerInstance.logStartTime };
}





/*
// Create first new logger
let { logger, logStartTime } = setupLogger(CONFIG.LOGGING);
logger.log('Initial logger setup');
console.log('Logger started at:', new Date(logStartTime));

// Later in this project, use this to get the existing logger
let { logger, logStartTime } =  getLogger();
logger.log('Using existing logger');
console.log('This logger was started at:', new Date(logStartTime));

// Later in this project, when you need a freash logger, do this
let { logger, logStartTime } = resetLogger(CONFIG.LOGGING);
logger.log('New logger instance created');
console.log('New logger started at:', new Date(logStartTime));
*/

