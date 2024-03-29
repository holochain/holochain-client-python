{
    description = "Flake for Holochain client development";

    inputs = {
        versions.url = "github:holochain/holochain?dir=versions/0_2";

        versions.inputs.holochain.url = "github:holochain/holochain/holochain-0.2.6";

        holochain = {
            url = "github:holochain/holochain";
            inputs.versions.follows = "versions";
        };

        nixpkgs.follows = "holochain/nixpkgs";
    };

    outputs = inputs @ { ... }:
    inputs.holochain.inputs.flake-parts.lib.mkFlake { inherit inputs; }
    {
        systems = builtins.attrNames inputs.holochain.devShells;
        perSystem = { config, pkgs, system, ... }: {
            devShells.default = pkgs.mkShell {
                inputsFrom = [
                    inputs.holochain.devShells.${system}.holonix
                ];
                packages = [
                    (pkgs.python3.withPackages (python-pkgs: [
                        python-pkgs.pip
                        python-pkgs.poetry-core
                    ]))
                    pkgs.poetry
                    pkgs.nodejs_20
                ];
            };
        };
    };
}
