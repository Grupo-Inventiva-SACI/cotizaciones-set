create or replace PROCEDURE WSP_TIPOS_CAMBIOS_SET(p_body    IN  CLOB,
                                                  p_mensaje OUT VARCHAR2) IS

                  /*Desarrollado en Base de Datos 21c
                         Oracle Apex ver. 23.1*/

                      /*########################*/
                      /*      by Ronald P.      */
                      /*     Noviembre 2023     */
                      /*########################*/

    --Variables importantes
    j               apex_json.t_values;
    pContCabecera   NUMBER(3);
    pContMoneda     NUMBER(3);
    vDescMoneda     VARCHAR2(20);
    vExiste         VARCHAR2(1);

    --Tipos de cambio
    vFechaAux       VARCHAR2(30);
    vFechaCambio    [SCHEMA].[TABLE_NAME].FEC_TIPO_CAMBIO%TYPE;
    vTipoCambio     [SCHEMA].[TABLE_NAME].TIPO_CAMBIO%TYPE;
    vIdMoneda       [SCHEMA].[TABLE_NAME].ID_MONEDA%TYPE;
    vCompra         [SCHEMA].[TABLE_NAME].VAL_COMPRA%TYPE;
    vVenta          [SCHEMA].[TABLE_NAME].VAL_VENTA%TYPE;
    
    --Monedas
    vSiglas         [SCHEMA].[TABLE_NAME].SIGLAS%TYPE;

BEGIN
    --Inicio del Programa Principal:

    --Inicializaci?n de variables y parametros
    vFechaCambio  := NULL;
    pContCabecera := NULL;
    vExiste       := 'N';
    vTipoCambio   := 'C'; -- Para contabilidad por que es directo de la SET

    --Lectura del JSON.
    apex_json.parse(j, p_body);
                                            
    pContCabecera  := apex_json.get_count   (p_path   => '.',
                                             p_values => j); 
                                             
    
    vFechaAux      := apex_json.get_members (p_path   => '.',
                                             p_values => j)
                                            (pContCabecera);
                                            
    pContMoneda    := apex_json.get_count   (p_path   => vFechaAux,
                                             p_values => j);
    
    vFechaCambio   := TO_CHAR(to_date(replace(vFechaAux,'"',''),'YYYY-MM-DD'), 'DD/MM/YYYY');
                                             
    dbms_output.put_line('Leyendo JSON... '||  'Items en total: '|| pContCabecera);

    FOR a IN 1.. pContMoneda LOOP
      
        vIdMoneda      := NULL;
        vDescMoneda    := NULL;
    
        vDescMoneda    := apex_json.get_members (p_path   => vFechaAux,
                                                 p_values => j)
                                                (a);
                                                 
        vVenta         := apex_json.get_number  (p_path   => vFechaAux||'.'||vDescMoneda||'.sale',
                                                 p_values => j);
                                                
        vCompra        := apex_json.get_number  (p_path   => vFechaAux||'.'||vDescMoneda||'.purchase',
                                                 p_values => j);
        
        dbms_output.put_line('Desc. moneda: ' || vDescMoneda || ' | con valor en compra: ' || vCompra ||' y venta: ' ||vVenta);
                                                 
        CASE
            WHEN upper(vDescMoneda) = 'USD' THEN vSiglas := 'USD';
            WHEN upper(vDescMoneda) = 'EUR' THEN vSiglas := 'EUR';
            WHEN upper(vDescMoneda) = 'BRL' THEN vSiglas := 'BRL';
            WHEN upper(vDescMoneda) = 'ARP' THEN vSiglas := 'ARS';
            ELSE vSiglas := 'NONE';
        END CASE;
        
        dbms_output.put_line('SIGLA ' || vSiglas);
        
        BEGIN
            SELECT M.ID
              INTO vIdMoneda
            FROM [SCHEMA].[TABLE_NAME] M
            WHERE M.SIGLAS = vSiglas;
        EXCEPTION
            WHEN OTHERS THEN
                 vIdMoneda := NULL;
        END;
        
        BEGIN
            SELECT 'S'
              INTO vExiste
            FROM [SCHEMA].[TABLE_NAME] T
            WHERE T.FEC_TIPO_CAMBIO = vFechaCambio
              AND T.ID_MONEDA       = vIdMoneda
              AND T.TIPO_CAMBIO     = vTipoCambio;
        EXCEPTION
            WHEN OTHERS THEN
                 vExiste := 'N';
        END;
        
        IF vExiste != 'S' AND vSiglas != 'NONE' THEN
            --raise_application_error(-20000,'STOP...');   
              
            BEGIN
              
                INSERT INTO [SCHEMA].[TABLE_NAME]( ID_MONEDA
                                                 ,TIPO_CAMBIO
                                                 ,FEC_TIPO_CAMBIO
                                                 ,VAL_VENTA
                                                 ,VAL_COMPRA
                                                 ,FEC_ALTA
                                                 ,COD_USUARIO_AUD)
                                          VALUES( vIdMoneda
                                                 ,vTipoCambio
                                                 ,vFechaCambio
                                                 ,vVenta
                                                 ,vCompra
                                                 ,SYSDATE
                                                 ,'AUTO');

                COMMIT;
                    
                p_mensaje := 'Se guardo el cambio ' || vDescMoneda || ' de la fecha ' || vFechaCambio || '.';
                    
            EXCEPTION
                WHEN DUP_VAL_ON_INDEX THEN
                    p_mensaje := 'Error C?digo: WS-1038. Ya existe el cambio ' || vDescMoneda || ' de la fecha ' || vFechaCambio || '.';
                    ROLLBACK;
                WHEN OTHERS THEN
                    p_mensaje := 'Ocurri? un error al guardar el cambio ' || vDescMoneda || ' de la fecha ' || vFechaCambio || '.';
                    ROLLBACK;
            END;
            
        END IF;
        
    END LOOP;
    
    p_mensaje := 'Ya se cargaron todos los cambios de la fecha ' || vFechaCambio;
    
EXCEPTION
    WHEN OTHERS THEN
         p_mensaje :=  ' Ha ocurrido un error en el proceso: ' || sqlerrm || ' ' || p_mensaje;

END;
