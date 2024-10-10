import fs from 'fs';
import path from 'path';

export function getLatestJsonFile(cctvConfig, logger) {
    const files = fs.readdirSync(cctvConfig.jsonDirectory)
      .filter(file => file.startsWith('cctv_sessions_') && file.endsWith('.json'));
  
    if (files.length === 0) {
      logger.error('No JSON files found in the directory.');
      return null;
    }
  
    const latestFile = files.reduce((latest, file) => {
      return fs.statSync(path.join(cctvConfig.jsonDirectory, file)).mtime.getTime() >
             fs.statSync(path.join(cctvConfig.jsonDirectory, latest)).mtime.getTime() ? file : latest;
    });
  
    logger.log(`Latest JSON file: ${latestFile}`);
    return path.join(cctvConfig.jsonDirectory, latestFile);
}

export function deleteOldJsonFiles(cctvConfig, logger) {
    const now = Date.now();
    const maxAge = cctvConfig.jsonMaxAgeHours * 60 * 60 * 1000;
    fs.readdirSync(cctvConfig.jsonDirectory).forEach(file => {
        if (file.startsWith('cctv_sessions_') && file.endsWith('.json')) {
            const filePath = path.join(cctvConfig.jsonDirectory, file);
            if (now - fs.statSync(filePath).mtime.getTime() > maxAge) {
                fs.unlinkSync(filePath);
                logger.log(`Deleted old JSON file: ${file}`);
            }
        }
    });
}