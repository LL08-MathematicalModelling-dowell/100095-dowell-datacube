import { v4 as uuidv4 } from 'uuid';

export const apiKeyGenerator = async () => {
    return uuidv4();
};
