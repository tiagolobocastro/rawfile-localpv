let
  sources = import ./nix/sources.nix;
  pkgs = import sources.nixpkgs {};
in
pkgs.mkShell {
  name = "rawfile-deploy-shell";
  buildInputs = with pkgs; [
    kubernetes-helm-wrapped
  ];
}
