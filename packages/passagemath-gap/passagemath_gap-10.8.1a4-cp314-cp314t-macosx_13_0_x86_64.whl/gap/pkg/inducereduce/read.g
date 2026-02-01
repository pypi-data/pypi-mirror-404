#
# InduceReduce: Unger's Algorithm to compute character tables of finite groups
#
# Reading the implementation part of the package.
#

if not IsBound(ComputeAllPowerMaps) then
# for compatibility with GAP versions before 4.15.1
BindGlobal( "ComputeAllPowerMaps", function( tbl )
  tbl:= UnderlyingGroup( tbl );
  if not HasDixonRecord( tbl ) then
    DxCalcAllPowerMaps( DixonRecord( tbl ) );
  fi;
end );
fi;

ReadPackage( "InduceReduce", "lib/InduceReduce.gi");
