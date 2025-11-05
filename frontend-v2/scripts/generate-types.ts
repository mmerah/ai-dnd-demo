/**
 * Generate TypeScript types from backend Pydantic models
 *
 * This script fetches JSON schemas from the backend /api/schemas endpoint
 * and converts them to TypeScript interfaces using json-schema-to-typescript.
 *
 * Usage:
 *   npm run generate:types
 *
 * Requirements:
 *   - Backend server must be running on http://localhost:8123
 */

import { writeFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { compile } from 'json-schema-to-typescript';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const BACKEND_URL = 'http://localhost:8123';
const OUTPUT_DIR = join(__dirname, '..', 'src', 'types', 'generated');

interface SchemaMap {
    [key: string]: unknown;
}

async function fetchSchemas(): Promise<SchemaMap> {
    console.log(`Fetching schemas from ${BACKEND_URL}/api/schemas...`);

    const response = await fetch(`${BACKEND_URL}/api/schemas`);

    if (!response.ok) {
        throw new Error(`Failed to fetch schemas: ${response.status} ${response.statusText}`);
    }

    return await response.json();
}

async function generateTypeFile(name: string, schema: unknown): Promise<string> {
    const ts = await compile(schema as any, name, {
        bannerComment: `/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */\n/* Generated on ${new Date().toISOString()} */`,
        style: {
            semi: true,
            singleQuote: true,
            tabWidth: 2
        },
        strictIndexSignatures: true,
        unknownAny: false,
        format: true
    });

    return ts;
}

async function generateAllTypes() {
    try {
        // Ensure output directory exists
        mkdirSync(OUTPUT_DIR, { recursive: true });

        // Fetch schemas from backend
        const schemas = await fetchSchemas();

        console.log(`Found ${Object.keys(schemas).length} schemas to convert`);

        // Generate TypeScript for each schema
        const exports: string[] = [];
        for (const [name, schema] of Object.entries(schemas)) {
            console.log(`  Generating ${name}.ts...`);

            const ts = await generateTypeFile(name, schema);
            const filename = `${name}.ts`;
            const filepath = join(OUTPUT_DIR, filename);

            writeFileSync(filepath, ts);
            exports.push(`export * from './${name}.js';`);

            console.log(`    ✓ Written to ${filename}`);
        }

        // Generate index.ts that re-exports all types
        const indexContent = [
            '/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */',
            `/* Generated on ${new Date().toISOString()} */`,
            '',
            ...exports
        ].join('\n');

        writeFileSync(join(OUTPUT_DIR, 'index.ts'), indexContent);
        console.log(`  ✓ Generated index.ts`);

        console.log('\n✨ Successfully generated TypeScript types from backend!\n');

    } catch (error) {
        if (error instanceof Error) {
            if (error.message.includes('fetch')) {
                console.error('\n❌ Failed to connect to backend server');
                console.error('   Make sure the backend is running on http://localhost:8123\n');
                console.error(`   Error: ${error.message}\n`);
            } else {
                console.error('\n❌ Type generation failed');
                console.error(`   Error: ${error.message}\n`);
                if (error.stack) {
                    console.error(error.stack);
                }
            }
        } else {
            console.error('\n❌ Unknown error:', error);
        }
        process.exit(1);
    }
}

// Run the generator
generateAllTypes();
