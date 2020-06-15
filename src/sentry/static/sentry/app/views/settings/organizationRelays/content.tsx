import React from 'react';
import styled from '@emotion/styled';

import {t} from 'app/locale';
import space from 'app/styles/space';
import Button from 'app/components/button';
import EmptyMessage from 'app/views/settings/components/emptyMessage';
import {IconDelete, IconEdit, IconWarning} from 'app/icons';

import Time from './time';
import {Relay} from './types';

type Props = {
  relays: Array<Relay>;
  onEdit: (publicKey: string) => () => void;
  onDelete: (publicKey: string) => () => void;
};

const Content = ({relays, onEdit, onDelete}: Props) => {
  if (relays.length === 0) {
    return (
      <EmptyMessage
        icon={<IconWarning size="xl" />}
        description={t('You have no relays')}
      />
    );
  }

  return (
    <React.Fragment>
      {relays.map(
        ({publicKey: key, name, created, lastUsed, firstUsed, lastModified}) => (
          <Wrapper key={key}>
            <Info>
              <InfoItem>
                <Name>{name}</Name>
              </InfoItem>
              <InfoItem>
                <PublicKey>{key}</PublicKey>
              </InfoItem>
              <InfoItem>
                <Time label={t('Added on:')} date={created} />
              </InfoItem>
              <InfoItem>
                <Time label={t('First used:')} date={firstUsed} />
              </InfoItem>
              <InfoItem>
                <Time label={t('Last used:')} date={lastUsed} />
              </InfoItem>
              <InfoItem>
                <Time label={t('Last modified:')} date={lastModified} />
              </InfoItem>
            </Info>
            <Actions>
              <Button
                title={t('Edit Rule')}
                label={t('Edit Rule')}
                size="small"
                icon={<IconEdit />}
                onClick={onEdit(key)}
              />
              <Button
                title={t('Delete Rule')}
                label={t('Delete Rule')}
                onClick={onDelete(key)}
                size="small"
                icon={<IconDelete />}
              />
            </Actions>
          </Wrapper>
        )
      )}
    </React.Fragment>
  );
};

export default Content;

const Name = styled('h4')`
  font-size: ${p => p.theme.fontSizeLarge} !important;
  font-weight: 600;
  margin-bottom: 0 !important;
  color: ${p => p.theme.gray600};
`;

const PublicKey = styled('h5')`
  font-size: ${p => p.theme.fontSizeMedium} !important;
  font-weight: 400;
  margin-bottom: 0 !important;
`;

const Wrapper = styled('div')`
  display: grid;
  grid-template-columns: 1fr max-content;
  align-items: center;
  border-bottom: 1px solid ${p => p.theme.borderDark};
  padding: ${space(2)};
  :last-child {
    border-bottom: 0;
  }
`;

const Info = styled('div')`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-gap: ${space(1)};
  > *:nth-child(1),
  > *:nth-child(2) {
    grid-column: span 4;
  }
`;

const Actions = styled('div')`
  display: grid;
  grid-template-columns: repeat(2, max-content);
  grid-gap: ${space(1)};
`;

const InfoItem = styled('div')`
  display: flex;
  align-items: center;
  height: 100%;
`;
