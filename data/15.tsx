/**
 * Apache License 2.0
 * Copyright 2024 React Team
 */

import React from 'react';

interface Props {
  name: string;
}

function Profile({ name }: Props) {
  const handleClick = (e: React.MouseEvent) => {
    console.log('Clicked', name);
  };

  return (
    <div onClick={handleClick}>
      Hello, {name}
    </div>
  );
}

export default Profile;
