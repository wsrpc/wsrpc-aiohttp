import babel from 'rollup-plugin-babel';


export default [
  {
    input: 'build/js/wsrpc.js',
    output: {
      file: 'build/js/dist/wsrpc.js',
      name: 'WSRPC',
      format: 'umd',
      sourcemap: true
    },
    plugins: [
      babel({
		babelrc: false,
		compact: false,
        plugins: ["@babel/plugin-proposal-class-properties"],
        presets: ["@babel/preset-env"]
      }),
    ]
  }
];
