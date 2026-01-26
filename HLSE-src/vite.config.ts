import { defineConfig } from 'vite';
import Vue from '@vitejs/plugin-vue';
import { viteSingleFile } from 'vite-plugin-singlefile';

export default defineConfig(({ command }) =>
{
    const baseConfig = {
        // base: process.env.BASE_URL || 'https://github.com/',
        root: 'src/client',
        server: {
            port: 8080
        },
        build: {
            sourcemap: process.env.SOURCE_MAP === 'true',
            outDir: '../../dist/client',
            emptyOutDir: true,
            chunkSizeWarningLimit: 600,
            cssCodeSplit: true
        },
        plugins: [
            Vue()
        ]
    };

    if(command === 'build')
    {
        return { ...baseConfig,
            plugins: [
                Vue(),
                viteSingleFile()
            ] };
    }
    else 
    {
        return baseConfig;
    }
});
