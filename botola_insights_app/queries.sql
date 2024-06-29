SELECT [p].[playerName] as GoalKeeperName
       ,[p2].[playerName]
       ,[m].[matcheId]
       ,CONCAT([m].[homeName], ' - ', [m].[awayName]) as matchName
      ,[EndY]
      ,[EndX]
      ,[xgot]
      ,[goalType]
      ,[xg]
      ,[timeSeconds]
      ,[time]
      ,[shotType]
      ,[reversedPeriodTime]
      ,[DrawId]
      ,[goalMouthLocation]
      ,[bodyPart]
      ,[DatumAddedTime]
      ,[BlockCoordinatesZ]
      ,[BlockCoordinatesY]
      ,[BlockCoordinatesX]
      ,[StartY]
      ,[StartX]
      ,[PlayerCoordinatesZ]
      ,[PlayerCoordinatesY]
      ,[PlayerCoordinatesX]
      ,[BlockY]
      ,[GoalMouthCoordinatesY]
      ,[addedTime]
      ,[GoalMouthCoordinatesZ]
      ,[GoalMouthCoordinatesX]
      ,[BlockX]
      ,[isHome]
  FROM [dim].[AxeLineUps] l 
  JOIN [dim].[AxeMatche] m ON [l].[matcheId]=[m].[matcheId]
  JOIN [dim].[FactShotMap] s ON [s].[matcheId]=[m].[matcheId]
  JOIN [dim].[AxePlayer] p2 on [p2].[PlayerId]=[s].[PlayerId]
  JOIN [dim].[AxePlayer] p on [p].[PlayerId]=[l].[PlayerId]
  WHERE [p].[position] = 'G'
  AND [p].[teamId]=[p2].[teamId]
  AND CONCAT([m].[homeName], ' - ', [m].[awayName]) = 'Raja Club Athletic - Jeunesse Sportive Soualem'
  AND [l].[substitute]=0;

-- ====================
SELECT DISTINCT([playerid])
      ,[position]
      ,[shortName]
      ,[playerName]
      ,[substitute]
      ,[rating]
      ,[saves]
      ,[mactheId]
      ,[formation]
  FROM [stg].[MatcheLineUps]
  WHERE [position]='G'