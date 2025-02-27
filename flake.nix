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
          pname = "semgrep-search";
          propagatedBuildInputs = deps;
          pyproject = true;
          pythonRelaxDeps = true;
          src = ./.;
          version = "1.1.0";
          nativeBuildInputs = with pkgs.python3Packages; [
            poetry-core
          ];
        };

        # nix develop
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pkgs.python3
            packages.default
          ] ++ deps;
        };

        # nix run
        apps.default = {
          type = "app";
          program = "${packages.default}/bin/sgs";
        };
      }
    );
}
