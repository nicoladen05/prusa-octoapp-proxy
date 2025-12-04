{
  description = "Prusa to OctoApp Proxy";

  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

  outputs =
    { self, ... }@inputs:
    let
      supportedSystems = [
        "x86_64-linux"
        "aarch64-linux"
      ];

      forEachSupportedSystem =
        f:
        inputs.nixpkgs.lib.genAttrs supportedSystems (
          system:
          f {
            inherit system;
            pkgs = import inputs.nixpkgs {
              inherit system;
              config.allowUnfree = true;
            };
          }
        );
    in
    {
      packages = forEachSupportedSystem (
        { pkgs, ... }:
        {
          default = pkgs.python313Packages.buildPythonApplication {
            pname = "prusa-octoapp-proxy";
            version = "0.1.0";
            pyproject = true;
            src = ./.;

            nativeBuildInputs = with pkgs.python313Packages; [
              setuptools
              wheel
            ];

            propagatedBuildInputs = with pkgs.python313Packages; [
              cryptography
              fastapi
              httpx
              requests
              uvicorn
              websockets
              wsproto
            ];
          };
        }
      );

      nixosModules.default = { config, lib, pkgs, ... }:
      let
        cfg = config.services.prusa-octoapp-proxy;
      in
      {
        options.services.prusa-octoapp-proxy = {
          enable = lib.mkEnableOption "Enable the Prusa to OctoApp Proxy service";
          port = lib.mkOption {
            type = lib.types.port;
            default = 5000;
            description = "Port to listen on";
          };
          openFirewall = lib.mkOption {
            type = lib.types.bool;
            default = false;
            description = "Whether to open the firewall for the Prusa to OctoApp Proxy service";
          };
          package = lib.mkOption {
            type = lib.types.package;
            default = self.packages.${pkgs.system}.default;
            description = "The package to use for the Prusa to OctoApp Proxy service";
          };
          user = lib.mkOption {
            type = lib.types.str;
            default = "prusa-octoapp-proxy";
            description = "The user to run the Prusa to OctoApp Proxy service as";
          };
          group = lib.mkOption {
            type = lib.types.str;
            default = "prusa-octoapp-proxy";
            description = "The group to run the Prusa to OctoApp Proxy service as";
          };
        };

        config = lib.mkIf cfg.enable {
          users.users.${cfg.user} = {
            isSystemUser = true;
            inherit (cfg) group;
            description = "User for the Prusa to OctoApp Proxy service";
          };
          users.groups.${cfg.group} = {};

          systemd.services.prusa-octoapp-proxy = {
            description = "Prusa to OctoApp Proxy service";
            after = [ "network.target" ];
            wantedBy = [ "multi-user.target" ];
            serviceConfig = {
              Type = "simple";
              User = cfg.user;
              Group = cfg.group;
              ExecStart = "${cfg.package}/bin/prusa-octoapp-proxy";
              Restart = "always";
            };
          };

          networking.firewall.allowedTCPPorts = lib.mkIf cfg.openFirewall [ cfg.port ];
        };
      };
    };
}
