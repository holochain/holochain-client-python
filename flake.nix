{
    description = "Flake for Holochain client development (Holochain 0.6)";

    inputs = {
        holonix.url = "github:holochain/holonix?ref=main-0.6";

        nixpkgs.follows = "holonix/nixpkgs";
        flake-parts.follows = "holonix/flake-parts";
    };

    outputs = inputs @ { flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; }
    {
        systems = builtins.attrNames inputs.holonix.devShells;
        perSystem = { inputs', pkgs, system, ... }: {
            devShells.default = pkgs.mkShell {
                packages = (with inputs'.holonix.packages; [
                    holochain
                    hc
                    lair-keystore
                    rust # Rust toolchain with the wasm32 target for building zomes
                ]) ++ (with pkgs; [
                    (python3.withPackages (ps: [ ps.pip ps.poetry-core ]))
                    poetry
                    nodejs_20
                ]);
            };
        };
    };
}
