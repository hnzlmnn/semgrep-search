{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.flake-utils.url = "github:numtide/flake-utils";

  outputs =
    { ... }@inputs:
    inputs.flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import inputs.nixpkgs { inherit system; };
        deps = with pkgs.python3Packages; [
          babel
          oras
          poetry-core
          poetry-core
          pyyaml
          requests
          rich
          ruamel-yaml
          semver
          tinydb
          tomli
        ];
      in
      rec {
        # nix build
        packages.default = pkgs.python3Packages.buildPythonPackage {
          dependencies = deps;
          pname = "semgrep-search";
          pyproject = true;
          pythonRelaxDeps = true;
          src = ./.;
          version = "1.1.0";
        };

        # nix develop --command $SHELL
        devShells.default = pkgs.mkShell {
          dependencies = [ packages.default ] ++ deps;
        };

        # nix run . -- search
        apps.default = {
          type = "app";
          program = "${packages.default}/bin/sgs";
        };
      }
    );
}
