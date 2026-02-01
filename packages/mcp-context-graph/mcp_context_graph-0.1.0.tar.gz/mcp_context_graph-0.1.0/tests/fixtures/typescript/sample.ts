/**
 * Sample TypeScript file for testing tree-sitter parsing.
 */

import { readFile, writeFile } from 'fs/promises';
import * as path from 'path';

interface User {
    id: number;
    name: string;
    email: string;
}

type ProcessResult<T> = {
    success: boolean;
    data?: T;
    error?: string;
};

class UserService {
    private users: Map<number, User> = new Map();

    constructor() {
        this.initialize();
    }

    private initialize(): void {
        console.log('UserService initialized');
    }

    async getUser(id: number): Promise<User | undefined> {
        return this.users.get(id);
    }

    async createUser(user: User): Promise<ProcessResult<User>> {
        if (this.users.has(user.id)) {
            return { success: false, error: 'User already exists' };
        }
        this.users.set(user.id, user);
        return { success: true, data: user };
    }

    async deleteUser(id: number): Promise<boolean> {
        return this.users.delete(id);
    }
}

function calculateTotal(prices: number[]): number {
    return prices.reduce((sum, price) => sum + price, 0);
}

const processData = async (filePath: string): Promise<string> => {
    const content = await readFile(filePath, 'utf-8');
    return content.trim();
};

export async function main(): Promise<void> {
    const service = new UserService();
    
    const result = await service.createUser({
        id: 1,
        name: 'John Doe',
        email: 'john@example.com'
    });
    
    console.log('Result:', result);
    
    const total = calculateTotal([10, 20, 30]);
    console.log('Total:', total);
}

export { UserService, User, ProcessResult };
